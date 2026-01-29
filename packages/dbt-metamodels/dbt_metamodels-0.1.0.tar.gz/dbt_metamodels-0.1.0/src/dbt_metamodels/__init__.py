import dataclasses
import os


def add_files(files, project_parser_files):
    from dbt.parser.schemas import SchemaSourceFile, SourceFile
    from dbt.contracts.files import ParseFileType

    def _replace_with_name(path: str, model_name: str) -> str:
        return os.path.join(os.path.dirname(path), model_name + '.sql')

    new_files = {}
    for file_id, f in files.items():
        if isinstance(f, SchemaSourceFile):
            for model in f.dict_from_yaml.get('models', []):
                if model.get('metamodel'):
                    model_name = model['name']
                    new_path = dataclasses.replace(f.path, relative_path=_replace_with_name(f.path.relative_path, model_name))
                    new_file_id = _replace_with_name(f.file_id, model_name)
                    new_source_file = SourceFile(
                        path=new_path,
                        checksum=f.checksum,
                        project_name=f.project_name,
                        parse_file_type=ParseFileType.Model,
                        contents='{{ ' + model['metamodel'] + ' }}',
                    )
                    new_files[new_file_id] = new_source_file
                    project_parser_files[f.project_name]['ModelParser'].append(new_file_id)

    files.update(new_files)


def patch():
    from dbt.parser.read_files import ReadFilesFromFileSystem

    original = ReadFilesFromFileSystem.read_files
    if hasattr(original, 'patched'):
        return

    def _read_files(self):
        original(self)
        add_files(self.files, self.project_parser_files)

    _read_files.patched = True

    ReadFilesFromFileSystem.read_files = _read_files
