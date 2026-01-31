from setuptools import setup, Extension
import os

this_dir = os.path.abspath(os.path.dirname(__file__))

module = Extension(
    'imgprocessor.visual_analysis._native',
    sources=[os.path.join(this_dir, 'native_stub.c')],
)

if __name__ == '__main__':
    setup(
        name='imgprocessor_native',
        version='0.0.0',
        description='Native helpers for imgprocessor (optional)',
        ext_modules=[module],
    )
