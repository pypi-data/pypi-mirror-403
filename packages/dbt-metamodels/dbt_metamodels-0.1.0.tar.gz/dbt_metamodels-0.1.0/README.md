# dbt-metamodels

Define your dbt models in YAML using metamodels - a powerful way to generate SQL models from macro calls defined in your schema files.

## Overview

`dbt-metamodels` extends dbt to allow you to define models directly in your `schema.yml` files using a `metamodel` field. Instead of writing separate SQL files, you can reference macros that generate your SQL code, making your dbt project more maintainable and DRY.

## Installation

```bash
pip install dbt-metamodels
```

Or using `uv`:

```bash
uv add dbt-metamodels
```

## Usage

### 1. Define a Macro

First, create a macro that generates your SQL. For example, in `macros/demo_model.sql`:

```sql
{% macro demo_model(v) %}
select {{ v }} as id
{% endmacro %}
```

### 2. Define Models in schema.yml

Instead of creating separate `.sql` files, define your models in `schema.yml` using the `metamodel` field:

```yaml
version: 2

models:
  - name: my_first_dbt_model
    description: "A starter dbt model"
    metamodel: demo_model(1)
    columns:
      - name: id
        description: "The primary key for this table"

  - name: my_second_dbt_model
    description: "A starter dbt model"
    metamodel: demo_model(2)
    columns:
      - name: id
        description: "The primary key for this table"
```

### 3. Use Metamodels Alongside Regular Models

You can mix metamodels with regular SQL models. For example, `my_final_dbt_model.sql` can reference metamodel-generated models:

```sql
{{ config(materialized='table') }}

with source_data as (

    select * from {{ ref('my_first_dbt_model') }}
    union all
    select * from {{ ref('my_second_dbt_model') }}

)

select * from source_data
```

## How It Works

When dbt reads your project files:

1. The plugin intercepts the file reading process
2. It scans `schema.yml` files for models with a `metamodel` field
3. For each metamodel definition, it automatically generates a corresponding `.sql` file
4. The generated SQL wraps your macro call in `{{ }}` syntax
5. dbt then processes these generated files as if they were regular SQL models

## Example Project Structure

```
metamodels_demo/
├── dbt_project.yml
├── macros/
│   └── demo_model.sql          # Macro definition
├── models/
│   └── example/
│       ├── schema.yml          # Model definitions with metamodels
│       └── my_final_dbt_model.sql  # Regular SQL model
└── profiles.yml
```

## Benefits

- **DRY Principle**: Reuse macro logic across multiple models
- **YAML-First**: Define models alongside their documentation
- **Flexibility**: Mix metamodels with regular SQL models
- **Maintainability**: Update model logic in one place (the macro)

## Requirements

- Python >= 3.8
- dbt-core >= 1.5.0

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- [Homepage](https://github.com/klyusba/dbt-metamodels)
- [Repository](https://github.com/klyusba/dbt-metamodels.git)
- [Issues](https://github.com/klyusba/dbt-metamodels/issues)
