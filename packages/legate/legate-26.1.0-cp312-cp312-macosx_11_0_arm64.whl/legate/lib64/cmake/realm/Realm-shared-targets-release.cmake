#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Realm::Realm" for configuration "Release"
set_property(TARGET Realm::Realm APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Realm::Realm PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib64/librealm-legate.25.6.1.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/librealm-legate.25.dylib"
  )

list(APPEND _cmake_import_check_targets Realm::Realm )
list(APPEND _cmake_import_check_files_for_Realm::Realm "${_IMPORT_PREFIX}/lib64/librealm-legate.25.6.1.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
