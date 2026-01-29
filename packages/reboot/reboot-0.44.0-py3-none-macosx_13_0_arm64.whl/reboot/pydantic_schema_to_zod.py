#!/usr/bin/env python3

import aiofiles
import importlib
import os
import types
from pydantic.fields import FieldInfo
from reboot.cli import terminal
from rebootdev.api import (
    API,
    COLLECTION_TYPE,
    PRIMITIVE_TYPE,
    Model,
    get_field_tag,
    snake_to_camel,
)
from typing import Literal, Optional, Type, Union, get_args, get_origin


def pydantic_to_zod(
    input: Type[Model] | PRIMITIVE_TYPE | COLLECTION_TYPE | None,
    path: str,
    tag: Optional[int] = None,
    method_request: bool = False,
    field_info: Optional[FieldInfo] = None,
) -> str:
    if input is None:
        if method_request:
            # For method requests, we use an empty object schema for now.
            return 'z.object({})'
        # Currently only used for methods with no response.
        return 'z.void()'

    origin = get_origin(input)
    args = get_args(input)

    if origin is Union or origin is types.UnionType:
        non_none_args = [arg for arg in args if arg is not type(None)]

        # Check if this is a discriminated union.
        discriminator = None
        if field_info is not None:
            discriminator = getattr(field_info, 'discriminator', None)

        if discriminator is not None:
            # This is a discriminated union.
            # Generate `z.discriminatedUnion('discriminator', [option1, option2, ...])`.
            camel_discriminator = snake_to_camel(discriminator)
            option_schemas = []
            for option_type in non_none_args:
                assert isinstance(option_type,
                                  type) and issubclass(option_type, Model)
                option_zod = pydantic_to_zod(
                    option_type,
                    f"{path}.{{{discriminator}}}",
                )
                option_schemas.append(option_zod)

            options_str = ',\n    '.join(option_schemas)
            output = f"z.discriminatedUnion('{camel_discriminator}', [\n    {options_str},\n  ])"

            if tag is not None:
                output += f'.meta({{ tag: {tag} }})'
            return output
        else:
            # This is an Optional[T].
            assert len(non_none_args) == 1

            # Generate the inner type without the tag, then add `.optional()` and
            # finally `.meta()`. This ensures meta is on the outermost schema, which
            # is required by `protoToZod` and `zodToProtoJson` converters.
            inner = pydantic_to_zod(non_none_args[0], path, tag=None)
            output = inner + '.optional()'
            if tag is not None:
                output += f'.meta({{ tag: {tag} }})'
            return output

    if isinstance(input, type) and issubclass(input, Model):
        # Help 'mypy' narrow the type.
        input_model: Type[Model] = input
        input_fields = input_model.model_fields
        if not input_fields:
            output = 'z.object({})'
        else:
            output_fields = []
            for field_name, field_info in input_fields.items():
                output_field_name = snake_to_camel(field_name)
                field_type = field_info.annotation
                field_tag = get_field_tag(field_info)

                assert field_tag is not None

                zod_object_field = pydantic_to_zod(
                    field_type,
                    f"{path}.{field_name}",
                    field_tag,
                    field_info=field_info,
                )

                output_fields.append(
                    f'{output_field_name}: {zod_object_field}'
                )

            output = 'z.object({\n    ' + ',\n    '.join(
                output_fields
            ) + ',\n  })'

        # The 'tag' might be missing if it is a nested type inside a
        # collection.
        if tag is not None:
            output += f'.meta({{ tag: {tag} }})'
        return output
    elif origin is dict:
        assert len(args) == 2
        key_type = args[0]
        value_type = args[1]

        assert key_type == str

        zod_value = pydantic_to_zod(
            value_type,
            f"{path}.[value]",
        )
        output = f'z.record(z.string(), {zod_value})'

        # The 'tag' might be missing if it is a nested type inside a
        # collection.
        if tag is not None:
            output += f'.meta({{ tag: {tag} }})'
        return output
    elif origin is list:
        assert len(args) == 1
        item_type = args[0]

        zod_item = pydantic_to_zod(
            item_type,
            f"{path}.[item]",
        )

        output = f'z.array({zod_item})'
        # The 'tag' might be missing if it is a nested type inside a
        # collection.
        if tag is not None:
            output += f'.meta({{ tag: {tag} }})'

        return output
    elif origin is Literal:
        for literal_value in args:
            if not isinstance(literal_value, str):
                terminal.fail(
                    f"Unexpected literal `{literal_value}` at `{path}`; "
                    f"only string literals are currently supported"
                )

        literal_values = ', '.join(f'"{v}"' for v in args)
        output = f'z.literal([{literal_values}])'

        # The 'tag' might be missing if it is a nested type inside a
        # collection.
        if tag is not None:
            output += f'.meta({{ tag: {tag} }})'

        return output
    else:
        if input == str:
            output = 'z.string()'
        elif input == int:
            output = 'z.number()'
        elif input == float:
            output = 'z.number()'
        elif input == bool:
            output = 'z.boolean()'
        else:
            terminal.fail(f"Unsupported type {input} at {path}")

        # The 'tag' might be missing if it is a nested type inside a
        # collection.
        if tag is not None:
            output += f'.meta({{ tag: {tag} }})'

        return output


async def generate_zod_file_from_api(
    filename: str,
    output_directory: str,
) -> Optional[str]:
    # In the 'rbt generate' we add every directory which contains schema
    # files to the 'sys.path', so we can directly import the file as a
    # module now.
    module_path = filename.rsplit('.py', 1)[0].replace(os.sep, '.')
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        terminal.fail(f"Failed to import module {module_path}: {e}")

    if not hasattr(module, 'api'):
        # It could be that the module does not define an API, but has some
        # shared code. In that case, we just skip it, but allow processing
        # further files.
        return None

    api: API = getattr(module, 'api')

    zod_file_name = filename.replace('.py', '_rbt_types.ts')

    zod_file_path = os.path.join(output_directory, zod_file_name)

    os.makedirs(os.path.dirname(zod_file_path), exist_ok=True)

    async with aiofiles.open(zod_file_path, 'w') as zod:
        await zod.write('import { z } from "zod/v4";\n')
        await zod.write(
            'import { reader, writer, transaction, workflow } from "@reboot-dev/reboot-api";\n\n'
        )

        # First pass: Generate all the exported schemas and types.
        for type_name, type_obj in api.get_types().items():
            # Generate state schema and type.
            await zod.write(f'export const {type_name}StateSchema = ')
            state_zod = pydantic_to_zod(
                type_obj.state,
                f"api.{type_name}.state",
            )
            await zod.write(f'{state_zod};\n\n')
            await zod.write(
                f'export type {type_name}State = z.infer<typeof {type_name}StateSchema>;\n\n'
            )

            # Generate method request and response schemas and types.
            for method_name, method_spec in type_obj.methods.items():
                camel_method_name = snake_to_camel(method_name)
                upper_camel_method_name = camel_method_name[0].upper(
                ) + camel_method_name[1:]

                await zod.write(
                    f'export const {type_name}{upper_camel_method_name}RequestSchema = '
                )
                request_zod = pydantic_to_zod(
                    method_spec.request,
                    f"api.{type_name}.methods.{method_name}.request",
                    method_request=True,
                )
                await zod.write(f'{request_zod};\n\n')
                await zod.write(
                    f'export type {type_name}{upper_camel_method_name}Request = z.infer<typeof '
                    f'{type_name}{upper_camel_method_name}RequestSchema>;\n\n'
                )

                await zod.write(
                    f'export const {type_name}{upper_camel_method_name}ResponseSchema = '
                )
                response_zod = pydantic_to_zod(
                    method_spec.response,
                    f"api.{type_name}.methods.{method_name}.response",
                )
                await zod.write(f'{response_zod};\n\n')
                await zod.write(
                    f'export type {type_name}{upper_camel_method_name}Response = z.infer<typeof '
                    f'{type_name}{upper_camel_method_name}ResponseSchema>;\n\n'
                )

        # Second pass: Generate the API structure using the exported schemas.
        for type_name, type_obj in api.get_types().items():
            # Open type section.
            await zod.write(f'export const {type_name} = {{\n')

            await zod.write(f'    state: {type_name}StateSchema,\n')

            # Open methods section.
            await zod.write('    methods: {\n')

            for method_name, method_spec in type_obj.methods.items():
                camel_method_name = snake_to_camel(method_name)
                upper_camel_method_name = camel_method_name[0].upper(
                ) + camel_method_name[1:]
                method_kind = method_spec.kind.value

                # Open method creation function section.
                await zod.write(
                    f'        {camel_method_name}: {method_kind}({{\n'
                )

                # Add factory if present.
                if method_spec.factory:
                    assert method_kind in ['writer', 'transaction']
                    await zod.write('            factory: {},\n')

                await zod.write(
                    f'            request: {type_name}{upper_camel_method_name}RequestSchema,\n',
                )
                await zod.write(
                    f'            response: {type_name}{upper_camel_method_name}ResponseSchema,\n',
                )

                # Close method creation function section.
                await zod.write('        }),\n')

            # Close methods section.
            await zod.write('    },\n')
            # Close type section.
            await zod.write('};\n\n')

        await zod.write('export const api = {\n')
        for type_name in api.get_types().keys():
            await zod.write(f'  {type_name},\n')
        await zod.write('};\n')

    return zod_file_name
