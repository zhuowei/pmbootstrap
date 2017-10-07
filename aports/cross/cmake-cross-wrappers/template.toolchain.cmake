set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR REPLACE_PROCESSOR_REPLACE)

set(CMAKE_SYSROOT /home/user/cross_sysroot/chroot_buildroot_REPLACE_CARCH_REPLACE)
#?
#set(CMAKE_STAGING_PREFIX /home/devel/stage)

set(gnutriple REPLACE_TRIPLE_REPLACE)
set(CMAKE_C_COMPILER ${gnutriple}-gcc)
set(CMAKE_CXX_COMPILER ${gnutriple}-g++)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

set(KDE_INSTALL_USE_QT_SYS_PATHS NO)
#set(QMAKE_EXECUTABLE /usr/lib/qt5/bin/qmake)
#set(QHelpGenerator_EXECUTABLE /usr/lib/qt5/bin/qhelpgenerator)
if(NOT TARGET Qt5Core_QCH)
    add_custom_target(Qt5Core_QCH)
endif()
