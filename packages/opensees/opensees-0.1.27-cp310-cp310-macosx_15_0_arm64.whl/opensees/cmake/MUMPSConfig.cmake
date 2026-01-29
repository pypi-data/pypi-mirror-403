
####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was config.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################

include(CMakeFindDependencyMacro)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR})

include(${CMAKE_CURRENT_LIST_DIR}/MUMPS-targets.cmake)

set(MUMPS_UPSTREAM_VERSION 5.8.0)
set(MUMPS_intsize64 OFF)
set(MUMPS_parallel OFF)
set(MUMPS_LAPACK_VENDOR )
set(MUMPS_SCALAPACK_VENDOR )

set(MUMPS_s_FOUND OFF)
set(MUMPS_d_FOUND ON)
set(MUMPS_c_FOUND OFF)
set(MUMPS_z_FOUND OFF)

if(MUMPS_parallel)
  find_dependency(MPI COMPONENTS C Fortran)

  if(NOT MUMPS_LAPACK_VENDOR MATCHES "^MKL")
    find_dependency(LAPACK COMPONENTS ${MUMPS_LAPACK_VENDOR})
  endif()

  find_dependency(SCALAPACK COMPONENTS ${MUMPS_SCALAPACK_VENDOR})
else()
  find_dependency(LAPACK COMPONENTS ${MUMPS_LAPACK_VENDOR})
  set(MUMPS_mpiseq_FOUND true)
endif()

set(MUMPS_Scotch_FOUND OFF)
if(MUMPS_Scotch_FOUND)
  find_dependency(Scotch COMPONENTS ESMUMPS)
endif()

set(MUMPS_METIS_FOUND OFF)
if(MUMPS_METIS_FOUND)
  find_dependency(METIS)
endif()

set(MUMPS_OpenMP_FOUND OFF)
if(MUMPS_OpenMP_FOUND)
  find_dependency(OpenMP)
endif()

check_required_components(MUMPS)
