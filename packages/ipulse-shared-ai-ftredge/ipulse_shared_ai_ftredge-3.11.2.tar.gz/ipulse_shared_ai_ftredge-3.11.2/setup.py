from setuptools import setup, find_packages

setup(
    name='ipulse_shared_ai_ftredge',
    version='3.11.2',  # Update shared_base dependency to 12.12.0 (includes Analyst DNA v2 enums)
    package_dir={'': 'src'},  # Specify the source directory
    packages=find_packages(where='src'),  # Look for packages in 'src'
    install_requires=[
        # Dependency chain: shared_base -> shared_core -> shared_ai
        'ipulse_shared_base_ftredge~=12.12.0',
        'ipulse_shared_core_ftredge~=27.9.0',  # Contains pydantic, fastapi, python-dateutil
    ],
    author='russlan.ramdowar',
    description='Shared AI models for the Pulse platform project. Using AI for financial advisory and investment management.',
    url='https://github.com/TheFutureEdge/ipulse_shared_ai',
)