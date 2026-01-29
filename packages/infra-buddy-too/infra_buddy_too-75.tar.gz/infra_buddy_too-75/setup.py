#!/usr/bin/env python
#   -*- coding: utf-8 -*-

from setuptools import setup
from setuptools.command.install import install as _install

class install(_install):
    def pre_install_script(self):
        pass

    def post_install_script(self):
        pass

    def run(self):
        self.pre_install_script()

        _install.run(self)

        self.post_install_script()

if __name__ == '__main__':
    setup(
        name = 'infra-buddy-too',
        version = '75',
        description = 'CLI for deploying micro-services',
        long_description = 'CLI for deploying micro-services',
        long_description_content_type = None,
        classifiers = [
            'Development Status :: 3 - Alpha',
            'Programming Language :: Python'
        ],
        keywords = '',

        author = '',
        author_email = '',
        maintainer = '',
        maintainer_email = '',

        license = 'Apache 2.0',

        url = 'https://github.com/Nudge-Security/infra-buddy',
        project_urls = {},

        scripts = ['scripts/infra-buddy'],
        packages = [
            'infra_buddy_too',
            'infra_buddy_too.aws',
            'infra_buddy_too.commands',
            'infra_buddy_too.commands.bootstrap',
            'infra_buddy_too.commands.deploy_cloudformation',
            'infra_buddy_too.commands.deploy_service',
            'infra_buddy_too.commands.generate_artifact_manifest',
            'infra_buddy_too.commands.generate_service_definition',
            'infra_buddy_too.commands.introspect',
            'infra_buddy_too.commands.validate_template',
            'infra_buddy_too.context',
            'infra_buddy_too.deploy',
            'infra_buddy_too.notifier',
            'infra_buddy_too.template',
            'infra_buddy_too.utility'
        ],
        namespace_packages = [],
        py_modules = [],
        entry_points = {},
        data_files = [],
        package_data = {
            'infra_buddy_too': ['template/builtin-templates.json']
        },
        install_requires = [
            'click',
            'boto3',
            'pydash==6.0.0',
            'jsonschema',
            'requests',
            'datadog',
            'botocore'
        ],
        dependency_links = [],
        zip_safe = True,
        cmdclass = {'install': install},
        python_requires = '>=3.6.0',
        obsoletes = [],
    )
