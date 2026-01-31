    Gary Oberbrunner (14):
          Add platform-specific installer generation for macOS and Windows
          Add Windows SxS manifest support for MSVC and clang-cl toolchains
          Refactor core architecture for clarity and simplicity
          Fix CI failures: multi-output target variables and test config
          Fix Windows manifest auxiliary input handling for clang-cl
          Fix MSVC SharedLibrary multi-output target variables
          Add /MANIFEST:EMBED to MSVC manifest auxiliary input handler
          Refactor MSVC and clang-cl toolchains to share common base class
          Fix Windows test coverage and add resource compiler to clang-cl
          Fix Windows compatibility for SharedLibrary linking and examples
          Simplify examples 01 and 04
          Make Generator.generate() default output_dir to project.build_dir
          Fix Makefile generator multi-output path handling on Windows
          Add compiler cache, presets, cross-compilation, and find_package

