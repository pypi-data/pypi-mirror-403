from setuptools import setup

setup(
    name="Time_PyP",
    version="1.0.3",
    author="Taha",
    description="کتابخانه مدیریت زمان پیشرفته - TimePythonProgramming",
    long_description="P_Time یک کتابخانه سبک برای کار با زمان در پایتون است. شامل کلاس TP برای مدیریت دقیق سال، ماه، روز، ساعت، دقیقه و ثانیه و ابزارهای کار با زمان سیستم (محلی و UTC)، تغییر زمان سیستم و غیره.",
    long_description_content_type="text/plain",
    py_modules=["Time_PyP"],
    packages=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Natural Language :: Persian"
    ],
    keywords="time datetime system-time utc localtime زمان ساعت time_pyp Time_PyP time",
    python_requires=">=3.8",
    install_requires=[],
    include_package_data=True,
    license="MIT"
)