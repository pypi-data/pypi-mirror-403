/*
 * Copyright (c) 2025 XLAB
 * All rights reserved.
 *
 * This file is part of trueform (trueform.polydera.com)
 *
 * Licensed for noncommercial use under the PolyForm Noncommercial
 * License 1.0.0.
 * Commercial licensing available via info@polydera.com.
 *
 * Auto-generated from CMakeLists.txt - do not edit manually
 */
#pragma once

#define POLYDERA_TF_VERSION_MAJOR 0
#define POLYDERA_TF_VERSION_MINOR 3
#define POLYDERA_TF_VERSION_PATCH 0

#define POLYDERA_TF_MAKE_VERSION(major, minor, patch) \
    ((major) * 100000 + (minor) * 100 + (patch))

#define POLYDERA_TF_VERSION \
    POLYDERA_TF_MAKE_VERSION(POLYDERA_TF_VERSION_MAJOR, \
                             POLYDERA_TF_VERSION_MINOR, \
                             POLYDERA_TF_VERSION_PATCH)

#define POLYDERA_TF_VERSION_STRING "0.3.0"

namespace tf {
inline constexpr int version_major = POLYDERA_TF_VERSION_MAJOR;
inline constexpr int version_minor = POLYDERA_TF_VERSION_MINOR;
inline constexpr int version_patch = POLYDERA_TF_VERSION_PATCH;
inline constexpr int version_number = POLYDERA_TF_VERSION;
inline constexpr const char* version = POLYDERA_TF_VERSION_STRING;
}
