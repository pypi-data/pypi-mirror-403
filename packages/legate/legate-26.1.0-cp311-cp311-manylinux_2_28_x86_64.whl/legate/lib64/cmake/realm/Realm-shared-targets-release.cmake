#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Realm::Realm" for configuration "Release"
set_property(TARGET Realm::Realm APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Realm::Realm PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "CUDA::cuda_driver;ucx::ucp;ucc::ucc"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib64/librealm-legate.so.25.6.1"
  IMPORTED_SONAME_RELEASE "librealm-legate.so.25"
  )

list(APPEND _cmake_import_check_targets Realm::Realm )
list(APPEND _cmake_import_check_files_for_Realm::Realm "${_IMPORT_PREFIX}/lib64/librealm-legate.so.25.6.1" )

# Import target "Realm::realm_bootstrap_p2p" for configuration "Release"
set_property(TARGET Realm::realm_bootstrap_p2p APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Realm::realm_bootstrap_p2p PROPERTIES
  IMPORTED_COMMON_LANGUAGE_RUNTIME_RELEASE ""
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib64/realm_bootstrap_p2p.so"
  IMPORTED_NO_SONAME_RELEASE "TRUE"
  )

list(APPEND _cmake_import_check_targets Realm::realm_bootstrap_p2p )
list(APPEND _cmake_import_check_files_for_Realm::realm_bootstrap_p2p "${_IMPORT_PREFIX}/lib64/realm_bootstrap_p2p.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
