import json
import logging
import pathlib
import shutil
from typing import Tuple, List, Dict, Generator, Optional, Union

import jinja2

from allure_markdown.config import config

class AllureMarkdown:

    def __init__(
            self,
            *,
            results_dir: Optional[str] = None,
            output: Optional[str] = None,
            title: Optional[str] = None,
            description: Optional[str] = None,
            custom_content: Optional[str] = None,
    ):
        self.results_dir = pathlib.Path(results_dir or config.results_dir)
        if not self.results_dir.exists():
            raise FileNotFoundError(f"Results directory '{self.results_dir}' does not exist")

        self.output = pathlib.Path(output or config.output)
        self.title = title or config.title
        self.description = description or config.description
        self.custom_content = custom_content
        
        self.output.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)

    def read_environment_file(self, environment_path: pathlib.Path) -> Dict[str, str]:
            environment = {}
            if not environment_path.exists():
                return environment
                
            try:
                with environment_path.open('r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            try:
                                key, value = line.split('=', 1)
                                environment[key.strip()] = value.strip()
                            except ValueError:
                                self.logger.warning(f"Invalid environment line {line_num}: {line}")
            except (IOError, UnicodeDecodeError) as e:
                self.logger.error(f"Failed to read environment file {environment_path}: {e}")
                
            return environment

    def _load_json_files(self) -> Generator[Dict, None, None]:
            json_files = list(self.results_dir.glob("*.json"))
            # 过滤掉categories文件
            json_files = [f for f in json_files if not f.name.startswith('categories')]
            
            for file_path in json_files:
                try:
                    with file_path.open('r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('name') and data.get('status'):
                            yield data
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.warning(f"Failed to load {file_path}: {e}")
                    continue

    def scan_allure_results(self) -> Tuple[List[Dict], Dict[str, str]]:
        # 读取环境信息
        environment_file = self.results_dir / 'environment.properties'
        environment = self.read_environment_file(environment_file)

        # 使用生成器加载JSON文件
        test_results = list(self._load_json_files())

        return test_results, environment

    def parse_test_results(self, test_results: List[Dict]) -> Tuple[Dict, List[Dict]]:
        summary = {
            'total': len(test_results),
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'broken': 0
        }

        fail_details = []

        for test in test_results:
            status = test.get('status', 'unknown')

            if status == 'passed':
                summary['passed'] += 1
            elif status == 'failed':
                summary['failed'] += 1
                fail_details.append(self._parse_fail_details(test))
            elif status == 'skipped':
                summary['skipped'] += 1
            elif status == 'broken':
                summary['broken'] += 1
                fail_details.append(self._parse_fail_details(test))

        return summary, fail_details

    def _process_attachment(self, attachment: Dict) -> Dict:
            at = {
                'name': attachment.get('name', 'Attachment'),
                'path': attachment.get('source', ''),
                'type': attachment.get('type', ''),
            }

            attachment_type = attachment.get('type', '')
            source_path = self.results_dir / attachment.get('source', '')

            try:
                if attachment_type == "text/plain":
                    if source_path.exists():
                        with source_path.open("r", encoding="utf-8") as f:
                            at['content'] = f.read(10000)
                elif attachment_type in ("video/mp4", "image/png"):
                    output_path = self.output.parent / attachment.get('source')
                    if source_path.exists():
                        shutil.copy2(source_path, output_path)
                        at['path'] = output_path.name
            except (IOError, OSError) as e:
                self.logger.warning(f"Failed to process attachment {source_path}: {e}")

            return at

    def _parse_fail_details(self, test: Dict) -> Dict:
        attachments = []
        
        if 'attachments' in test:
            attachments = [self._process_attachment(att) for att in test['attachments']]

        error_message = ''
        traceback = ''

        if 'statusDetails' in test:
            details = test['statusDetails']
            error_message = details.get('message', '')
            traceback = details.get('trace', '')

        return {
            'name': test.get('name', 'Unnamed Test'),
            'nodeid': test.get('fullName', ''),
            'status': test.get('status', 'unknown'),
            'error_message': error_message,
            'traceback': traceback,
            'attachments': attachments
        }

    def get_allure_results(self) -> Tuple[Dict, List[Dict], Dict[str, str]]:
        test_results, environment = self.scan_allure_results()
        summary, fail_details = self.parse_test_results(test_results)
        return summary, fail_details, environment

    def generate_markdown_report(
                self,
                *,
                summary: Dict,
                fail_details: List[Dict],
                environment: Dict[str, str],
                title: Optional[str] = None,
                description: Optional[str] = None,
                custom_content: Optional[str] = None,
                output_path: Optional[pathlib.Path] = None,
        ) -> None:
            env = jinja2.Environment(
                loader=jinja2.PackageLoader("allure_markdown", config.templates_path.as_posix()),
                autoescape=jinja2.select_autoescape()
            )

            template = env.get_template("report.md.j2")

            report_content = template.render(
                title=title,
                description=description,
                custom_content=custom_content,
                environment=environment,
                summary=summary,
                fail_details=fail_details
            )

            output_file = output_path or self.output
            with output_file.open('w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"Report generated successfully: {output_file}")

    def gen(self):
        print("Allure-Markdown: Converting Allure metadata to Markdown...")

        try:
            test_results, environment = self.scan_allure_results()

            if not test_results:
                print(f"Warning: No test results found in '{self.results_dir}'.")
                return 0

            summary, fail_details = self.parse_test_results(test_results)

            self.generate_markdown_report(
                summary=summary,
                fail_details=fail_details,
                environment=environment,
                title=self.title,
                description=self.description,
                custom_content=self.custom_content,
                output_path=self.output
            )
            return 0

        except Exception as e:
            print(f"Error: {str(e)}")
            return 1
