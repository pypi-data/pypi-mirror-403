"""Tests for TypeScript structure extraction."""

from tests.ts_structure import (
    extract_classes,
    extract_enums,
    extract_exports,
    extract_functions,
    extract_interfaces,
    extract_ts_structure,
    extract_type_aliases,
)


def test_extract_simple_interface(ts_parser):
    """Extract a simple interface with required and optional properties."""
    code = b"""
export interface Pet {
    id?: number;
    name: string;
    tag?: string;
}
"""
    result = extract_interfaces(code, ts_parser)

    assert result == [
        {
            "name": "Pet",
            "properties": [
                {"name": "id", "type": "number", "optional": True},
                {"name": "name", "type": "string", "optional": False},
                {"name": "tag", "type": "string", "optional": True},
            ],
        }
    ]


def test_extract_interface_with_array_type(ts_parser):
    """Extract interface with array type."""
    code = b"""
export interface Pet {
    tags: Array<string>;
    photoUrls: string[];
}
"""
    result = extract_interfaces(code, ts_parser)

    assert result == [
        {
            "name": "Pet",
            "properties": [
                {"name": "photoUrls", "type": "string[]", "optional": False},
                {"name": "tags", "type": "Array<string>", "optional": False},
            ],
        }
    ]


def test_extract_multiple_interfaces(ts_parser):
    """Extract multiple interfaces from same file."""
    code = b"""
export interface Pet {
    name: string;
}

export interface Category {
    id: number;
}
"""
    result = extract_interfaces(code, ts_parser)

    # Should be sorted by name for stable comparison
    assert len(result) == 2
    assert result[0]["name"] == "Category"
    assert result[1]["name"] == "Pet"


def test_extract_function_declaration(ts_parser):
    """Extract a function with parameters and return type."""
    code = b"""
export function PetFromJSON(json: any): Pet {
    return json;
}
"""
    result = extract_functions(code, ts_parser)

    assert result == [
        {
            "name": "PetFromJSON",
            "params": [{"name": "json", "type": "any"}],
            "return_type": "Pet",
        }
    ]


def test_extract_function_no_return_type(ts_parser):
    """Extract function without explicit return type."""
    code = b"""
export function log(message: string) {
    console.log(message);
}
"""
    result = extract_functions(code, ts_parser)

    assert result == [
        {
            "name": "log",
            "params": [{"name": "message", "type": "string"}],
            "return_type": None,
        }
    ]


def test_extract_multiple_functions(ts_parser):
    """Extract multiple functions sorted by name."""
    code = b"""
export function PetToJSON(pet: Pet): any {
    return pet;
}

export function PetFromJSON(json: any): Pet {
    return json;
}
"""
    result = extract_functions(code, ts_parser)

    assert len(result) == 2
    assert result[0]["name"] == "PetFromJSON"
    assert result[1]["name"] == "PetToJSON"


def test_extract_type_alias(ts_parser):
    """Extract a type alias."""
    code = b"""
export type PetStatus = 'available' | 'pending' | 'sold';
"""
    result = extract_type_aliases(code, ts_parser)

    assert result == [
        {
            "name": "PetStatus",
            "definition": "'available' | 'pending' | 'sold'",
        }
    ]


def test_extract_multiple_type_aliases(ts_parser):
    """Extract multiple type aliases sorted by name."""
    code = b"""
export type OrderStatus = 'placed' | 'approved';
export type PetStatus = 'available' | 'pending';
"""
    result = extract_type_aliases(code, ts_parser)

    assert len(result) == 2
    assert result[0]["name"] == "OrderStatus"
    assert result[1]["name"] == "PetStatus"


def test_extract_const_object_as_enum(ts_parser):
    """Extract const object used as enum."""
    code = b"""
export const PetStatusEnum = {
    Available: 'available',
    Pending: 'pending',
    Sold: 'sold'
} as const;
"""
    result = extract_enums(code, ts_parser)

    assert result == [
        {
            "name": "PetStatusEnum",
            "members": [
                {"name": "Available", "value": "'available'"},
                {"name": "Pending", "value": "'pending'"},
                {"name": "Sold", "value": "'sold'"},
            ],
        }
    ]


def test_extract_typescript_enum(ts_parser):
    """Extract TypeScript enum."""
    code = b"""
export enum Status {
    Active = 'active',
    Inactive = 'inactive'
}
"""
    result = extract_enums(code, ts_parser)

    assert result == [
        {
            "name": "Status",
            "members": [
                {"name": "Active", "value": "'active'"},
                {"name": "Inactive", "value": "'inactive'"},
            ],
        }
    ]


def test_extract_inline_exports(ts_parser):
    """Extract exports from export declarations."""
    code = b"""
export interface Pet {
    name: string;
}

export function PetFromJSON(json: any): Pet {
    return json;
}

export const PetStatusEnum = {} as const;
"""
    result = extract_exports(code, ts_parser)

    assert sorted(result) == ["Pet", "PetFromJSON", "PetStatusEnum"]


def test_extract_export_statement(ts_parser):
    """Extract exports from export statements."""
    code = b"""
interface Pet {
    name: string;
}

export { Pet };
"""
    result = extract_exports(code, ts_parser)

    assert result == ["Pet"]


def test_extract_reexports(ts_parser):
    """Extract re-exports from other modules."""
    code = b"""
export { Pet, Category } from './models';
export * from './runtime';
"""
    result = extract_exports(code, ts_parser)

    # Named exports should be captured, star exports noted
    assert "Pet" in result
    assert "Category" in result


def test_extract_class_with_properties(ts_parser):
    """Extract class with properties."""
    code = b"""
export class Configuration {
    basePath: string;
    apiKey?: string;

    constructor(config?: Partial<Configuration>) {}
}
"""
    result = extract_classes(code, ts_parser)

    assert len(result) == 1
    assert result[0]["name"] == "Configuration"
    assert {"name": "apiKey", "type": "string", "optional": True} in result[0]["properties"]
    assert {"name": "basePath", "type": "string", "optional": False} in result[0]["properties"]


def test_extract_class_with_methods(ts_parser):
    """Extract class with method signatures."""
    code = b"""
export class PetApi {
    getPet(petId: number): Promise<Pet> {
        return fetch('/pet/' + petId);
    }

    addPet(pet: Pet): Promise<void> {
        return fetch('/pet', { method: 'POST' });
    }
}
"""
    result = extract_classes(code, ts_parser)

    assert len(result) == 1
    methods = result[0]["methods"]
    assert len(methods) == 2
    assert {
        "name": "addPet",
        "params": [{"name": "pet", "type": "Pet"}],
        "return_type": "Promise<void>",
    } in methods
    assert {
        "name": "getPet",
        "params": [{"name": "petId", "type": "number"}],
        "return_type": "Promise<Pet>",
    } in methods


def test_extract_ts_structure_from_directory(ts_parser, tmp_path):
    """Extract structure from all .ts files in a directory."""
    # Create test files
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    (models_dir / "Pet.ts").write_text("""
export interface Pet {
    id?: number;
    name: string;
}

export function PetFromJSON(json: any): Pet {
    return json;
}
""")

    (models_dir / "index.ts").write_text("""
export { Pet, PetFromJSON } from './Pet';
""")

    result = extract_ts_structure(tmp_path, ts_parser)

    assert "models/Pet.ts" in result
    assert "models/index.ts" in result

    pet_structure = result["models/Pet.ts"]
    assert len(pet_structure["interfaces"]) == 1
    assert pet_structure["interfaces"][0]["name"] == "Pet"
    assert len(pet_structure["functions"]) == 1
    assert pet_structure["functions"][0]["name"] == "PetFromJSON"
