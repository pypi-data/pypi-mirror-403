# Copyright 2025 Stanford University, NVIDIA Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set(REALM_VERSION 25.6.1)


####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was RealmConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../" ABSOLUTE)

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

# Allow the application developer to choose between static and shared libraries
# if available by specifying 'static' or 'shared' component in find_package

set(Realm_known_comps static shared)
set(Realm_static_comp NO)
set(Realm_shared_comp NO)
foreach(_comp IN LISTS ${CMAKE_FIND_PACKAGE_NAME}_COMPONENTS)
  if(_comp IN_LIST Realm_known_comps)
    set(Realm_${_comp}_comp YES)
  else()
    set(${CMAKE_FIND_PACKAGE_NAME}_NOT_FOUND_MESSAGE
        "${CMAKE_FIND_PACKAGE_NAME} does not recognize ${_comp}"
    )
    set(${CMAKE_FIND_PACKAGE_NAME}_FOUND FALSE)
    return()
  endif()
endforeach()

if(Realm_static_comp AND Realm_shared_comp)
  set(${CMAKE_FIND_PACKAGE_NAME}_NOT_FOUND_MESSAGE
      "${CMAKE_FIND_PACKAGE_NAME} cannot request static and shared simultaneously"
  )
  set(${CMAKE_FIND_PACKAGE_NAME}_FOUND FALSE)
  return()
endif()

include(CMakeFindDependencyMacro)
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}")

# If Kokkos was used, it needs to be found regardless of shared or static since
# it's (unfortunately) part of the interface
# TODO(cperry): move this to be header only / optional, maybe after the c++ api
#               is implemented on top of the c api
set(REALM_USE_KOKKOS )
if(REALM_USE_KOKKOS)
  find_dependency(Kokkos)
endif()

macro(Realm_load_targets type)
  if(NOT EXISTS "${CMAKE_CURRENT_LIST_DIR}/Realm-${type}-targets.cmake")
    set(${CMAKE_FIND_PACKAGE_NAME}_NOT_FOUND_MESSAGE
        "${CMAKE_FIND_PACKAGE_NAME} '${type}' libraries requested, but not found"
    )
    set(${CMAKE_FIND_PACKAGE_NAME}_FOUND FALSE)
    return()
  endif()
  if(${type} STREQUAL "static")
    # Find all the static library dependencies needed
    # Use the installed Find* modules as a last resort for dependencies
    foreach(_dep Threads;cpptrace;Python3)
      find_dependency(${_dep})
    endforeach()
  endif()

  include("${CMAKE_CURRENT_LIST_DIR}/Realm-${type}-targets.cmake")
  set(${CMAKE_FIND_PACKAGE_NAME}_${type}_FOUND TRUE)
endmacro()

# If the user specified a static or shared, use that, otherwise guess with a reasonable default
if(Realm_static_comp)
  realm_load_targets(static)
elseif(Realm_shared_comp)
  realm_load_targets(shared)
elseif(BUILD_SHARED_LIBS)
  if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/Realm-shared-targets.cmake")
    realm_load_targets(shared)
  else()
    realm_load_targets(static)
  endif()
else()
  if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/Realm-static-targets.cmake")
    realm_load_targets(static)
  else()
    realm_load_targets(shared)
  endif()
endif()

check_required_components(Realm)
