# pylint: disable=import-error
from setuptools import setup, find_packages

setup(
    name='ipulse-shared-data-eng-ftredge',
    version="12.9.0",  # Updated dependencies: pydantic 2.12.5, GCS v3.8.0, BigQuery 3.40.0, shared_base 12.11.0
    package_dir={'': 'src'},  # Specify the source directory
    packages=find_packages(where='src'),  # Look for packages in 'src'
    install_requires=[
        # Dependency chain: shared_base contains google cloud logging and error reporting
        'ipulse_shared_base_ftredge~=12.11.0',
        'python-dateutil~=2.9.0',
        'pydantic~=2.12.5',  # Latest stable V2.x; critical for modern serialization
        'google-cloud-bigquery~=3.40.0',  # Performance fixes & newer Arrow support
        'google-cloud-storage~=3.8.0',  # MAJOR UPDATE (v3): crc32c checksums by default
        'google-cloud-pubsub~=2.34.0',  # Updates for flow control & OpenTelemetry
        'google-cloud-secret-manager~=2.26.0',
        'google-cloud-firestore~=2.23.0',  # Improved async & vector search support
        
    ],
    author='Russlan Ramdowar',
    description='Shared Data Engineering functions for the Pulse platform project. Using AI for financial advisory and investment management.',
    url='https://github.com/TheFutureEdge/ipulse_shared_data_eng'
)
