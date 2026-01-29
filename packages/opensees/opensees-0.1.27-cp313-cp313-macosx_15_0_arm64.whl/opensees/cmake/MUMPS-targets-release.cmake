#----------------------------------------------------------------
# Generated CMake target import file for configuration "RELEASE".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "MUMPS::MPISEQ" for configuration "RELEASE"
set_property(TARGET MUMPS::MPISEQ APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MUMPS::MPISEQ PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C;Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libmpiseq.a"
  )

list(APPEND _cmake_import_check_targets MUMPS::MPISEQ )
list(APPEND _cmake_import_check_files_for_MUMPS::MPISEQ "${_IMPORT_PREFIX}/lib/libmpiseq.a" )

# Import target "MUMPS::PORD" for configuration "RELEASE"
set_property(TARGET MUMPS::PORD APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MUMPS::PORD PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libpord.a"
  )

list(APPEND _cmake_import_check_targets MUMPS::PORD )
list(APPEND _cmake_import_check_files_for_MUMPS::PORD "${_IMPORT_PREFIX}/lib/libpord.a" )

# Import target "MUMPS::COMMON" for configuration "RELEASE"
set_property(TARGET MUMPS::COMMON APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MUMPS::COMMON PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C;Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libmumps_common.a"
  )

list(APPEND _cmake_import_check_targets MUMPS::COMMON )
list(APPEND _cmake_import_check_files_for_MUMPS::COMMON "${_IMPORT_PREFIX}/lib/libmumps_common.a" )

# Import target "MUMPS::DMUMPS" for configuration "RELEASE"
set_property(TARGET MUMPS::DMUMPS APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MUMPS::DMUMPS PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C;Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libdmumps.a"
  )

list(APPEND _cmake_import_check_targets MUMPS::DMUMPS )
list(APPEND _cmake_import_check_files_for_MUMPS::DMUMPS "${_IMPORT_PREFIX}/lib/libdmumps.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
