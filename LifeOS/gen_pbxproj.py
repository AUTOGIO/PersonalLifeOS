#!/usr/bin/env python3
"""Generate a complete, valid project.pbxproj for the LifeOS native app.
Preserves the original bundle id, deployment target, and signing settings.
Run on the Mac after staging files into lifeos/."""
import os

# Source files grouped by folder (relative to the LifeOS group / `lifeos/` dir)
GROUPS = {
    "App": ["LifeOSApp.swift", "RootView.swift"],
    "UI": ["HeaderBarView.swift", "TerminalComponents.swift", "TerminalTheme.swift"],
    "Models": ["Models.swift", "Extensions.swift", "AppData.swift"],
    "Persistence": ["SeedLoader.swift"],
    "ViewModels": ["MainViewModel.swift"],
    "Views": ["DashboardView.swift", "ActivitiesView.swift", "ProjectsView.swift",
              "HabitsView.swift", "KiteSessionsView.swift", "TidesView.swift",
              "WeeklyScheduleView.swift", "AnalyticsView.swift"],
}
RESOURCES = ["tides.json", "daily_plans.json"]  # in Resources/ group
ASSETS = "Assets.xcassets"

# Deterministic 24-hex IDs
def mk(prefix, n): return f"{prefix}{n:016X}"

build_files = []   # (buildId, name, fileRefId, phase)  phase in {Sources, Resources}
file_refs = []     # (fileRefId, name, fileType, path)
group_children = {}  # groupName -> list of fileRefIds
counter = [0x100]
def nid():
    counter[0] += 1
    return mk("DEAD", counter[0])

# Source files
src_build_ids = []
for group, files in GROUPS.items():
    group_children.setdefault(group, [])
    for fn in files:
        fref = nid(); bid = nid()
        file_refs.append((fref, fn, "sourcecode.swift", fn))
        build_files.append((bid, fn, fref, "Sources"))
        group_children[group].append(fref)
        src_build_ids.append(bid)

# Resources group (json)
group_children.setdefault("Resources", [])
res_build_ids = []
for fn in RESOURCES:
    fref = nid(); bid = nid()
    file_refs.append((fref, fn, "text.json", fn))
    build_files.append((bid, fn, fref, "Resources"))
    group_children["Resources"].append(fref)
    res_build_ids.append(bid)

# Assets
assets_ref = nid(); assets_build = nid()
file_refs.append((assets_ref, ASSETS, "folder.assetcatalog", ASSETS))
build_files.append((assets_build, ASSETS, assets_ref, "Resources"))
res_build_ids.append(assets_build)

# Fixed object ids
APP_PRODUCT = "A1000000000000000000000A"
FRAMEWORKS = "A10000000000000000000020"
MAINGROUP = "A10000000000000000000030"
LIFEOS_GROUP = "A10000000000000000000031"
PRODUCTS_GROUP = "A10000000000000000000032"
TARGET = "A10000000000000000000040"
CONFLIST_TARGET = "A10000000000000000000050"
SOURCES_PHASE = "A10000000000000000000060"
RESOURCES_PHASE = "A10000000000000000000061"
PROJECT = "A10000000000000000000070"
CONFLIST_PROJ = "A10000000000000000000071"
DBG_PROJ = "A10000000000000000000080"
REL_PROJ = "A10000000000000000000081"
DBG_TGT = "A10000000000000000000082"
REL_TGT = "A10000000000000000000083"

# Subgroup ids
subgroup_ids = {g: nid() for g in list(GROUPS.keys()) + ["Resources"]}

def esc(s): return s

lines = []
A = lines.append
A("// !$*UTF8*$!")
A("{")
A("archiveVersion = 1;")
A("classes = {")
A("};")
A("objectVersion = 56;")
A("objects = {")
A("")
A("/* Begin PBXBuildFile section */")
for bid, name, fref, phase in build_files:
    A(f"{bid} /* {name} in {phase} */ = {{isa = PBXBuildFile; fileRef = {fref} /* {name} */; }};")
A("/* End PBXBuildFile section */")
A("")
A("/* Begin PBXFileReference section */")
A(f"{APP_PRODUCT} /* LifeOS.app */ = {{isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = LifeOS.app; sourceTree = BUILT_PRODUCTS_DIR; }};")
for fref, name, ftype, path in file_refs:
    A(f"{fref} /* {name} */ = {{isa = PBXFileReference; lastKnownFileType = {ftype}; path = {path}; sourceTree = \"<group>\"; }};")
A("/* End PBXFileReference section */")
A("")
A("/* Begin PBXFrameworksBuildPhase section */")
A(f"{FRAMEWORKS} /* Frameworks */ = {{")
A("isa = PBXFrameworksBuildPhase;")
A("buildActionMask = 2147483647;")
A("files = (")
A(");")
A("runOnlyForDeploymentPostprocessing = 0;")
A("};")
A("/* End PBXFrameworksBuildPhase section */")
A("")
A("/* Begin PBXGroup section */")
# main group
A(f"{MAINGROUP} = {{")
A("isa = PBXGroup;")
A("children = (")
A(f"{LIFEOS_GROUP} /* LifeOS */,")
A(f"{PRODUCTS_GROUP} /* Products */,")
A(");")
A("sourceTree = \"<group>\";")
A("};")
# LifeOS group -> subgroups + assets
A(f"{LIFEOS_GROUP} /* LifeOS */ = {{")
A("isa = PBXGroup;")
A("children = (")
for g in ["App", "UI", "Models", "Persistence", "ViewModels", "Views", "Resources"]:
    A(f"{subgroup_ids[g]} /* {g} */,")
A(f"{assets_ref} /* {ASSETS} */,")
A(");")
A("path = LifeOS;")
A("sourceTree = \"<group>\";")
A("};")
# Products
A(f"{PRODUCTS_GROUP} /* Products */ = {{")
A("isa = PBXGroup;")
A("children = (")
A(f"{APP_PRODUCT} /* LifeOS.app */,")
A(");")
A("name = Products;")
A("sourceTree = \"<group>\";")
A("};")
# Subgroups
for g in ["App", "UI", "Models", "Persistence", "ViewModels", "Views", "Resources"]:
    A(f"{subgroup_ids[g]} /* {g} */ = {{")
    A("isa = PBXGroup;")
    A("children = (")
    for fref in group_children.get(g, []):
        # find name
        name = next(n for (r, n, t, p) in file_refs if r == fref)
        A(f"{fref} /* {name} */,")
    A(");")
    A(f"path = {g};")
    A("sourceTree = \"<group>\";")
    A("};")
A("/* End PBXGroup section */")
A("")
A("/* Begin PBXNativeTarget section */")
A(f"{TARGET} /* LifeOS */ = {{")
A("isa = PBXNativeTarget;")
A(f"buildConfigurationList = {CONFLIST_TARGET} /* Build configuration list for PBXNativeTarget \"LifeOS\" */;")
A("buildPhases = (")
A(f"{SOURCES_PHASE} /* Sources */,")
A(f"{FRAMEWORKS} /* Frameworks */,")
A(f"{RESOURCES_PHASE} /* Resources */,")
A(");")
A("buildRules = (")
A(");")
A("dependencies = (")
A(");")
A("name = LifeOS;")
A("productName = LifeOS;")
A(f"productReference = {APP_PRODUCT} /* LifeOS.app */;")
A("productType = \"com.apple.product-type.application\";")
A("};")
A("/* End PBXNativeTarget section */")
A("")
A("/* Begin PBXProject section */")
A(f"{PROJECT} /* Project object */ = {{")
A("isa = PBXProject;")
A("attributes = {")
A("BuildIndependentTargetsInParallel = 1;")
A("LastSwiftUpdateCheck = 1600;")
A("LastUpgradeCheck = 1600;")
A("TargetAttributes = {")
A(f"{TARGET} = {{")
A("CreatedOnToolsVersion = 16.0;")
A("};")
A("};")
A("};")
A(f"buildConfigurationList = {CONFLIST_PROJ} /* Build configuration list for PBXProject \"LifeOS\" */;")
A("compatibilityVersion = \"Xcode 14.0\";")
A("developmentRegion = en;")
A("hasScannedForEncodings = 0;")
A("knownRegions = (")
A("en,")
A("Base,")
A(");")
A(f"mainGroup = {MAINGROUP};")
A(f"productRefGroup = {PRODUCTS_GROUP} /* Products */;")
A("projectDirPath = \"\";")
A("projectRoot = \"\";")
A("targets = (")
A(f"{TARGET} /* LifeOS */,")
A(");")
A("};")
A("/* End PBXProject section */")
A("")
A("/* Begin PBXResourcesBuildPhase section */")
A(f"{RESOURCES_PHASE} /* Resources */ = {{")
A("isa = PBXResourcesBuildPhase;")
A("buildActionMask = 2147483647;")
A("files = (")
for bid in res_build_ids:
    name = next(n for (b, n, f, ph) in build_files if b == bid)
    A(f"{bid} /* {name} in Resources */,")
A(");")
A("runOnlyForDeploymentPostprocessing = 0;")
A("};")
A("/* End PBXResourcesBuildPhase section */")
A("")
A("/* Begin PBXSourcesBuildPhase section */")
A(f"{SOURCES_PHASE} /* Sources */ = {{")
A("isa = PBXSourcesBuildPhase;")
A("buildActionMask = 2147483647;")
A("files = (")
for bid in src_build_ids:
    name = next(n for (b, n, f, ph) in build_files if b == bid)
    A(f"{bid} /* {name} in Sources */,")
A(");")
A("runOnlyForDeploymentPostprocessing = 0;")
A("};")
A("/* End PBXSourcesBuildPhase section */")
A("")
A("/* Begin XCBuildConfiguration section */")

def proj_config(cid, name, debug):
    A(f"{cid} /* {name} */ = {{")
    A("isa = XCBuildConfiguration;")
    A("buildSettings = {")
    A("ALWAYS_SEARCH_USER_PATHS = NO;")
    A("CLANG_ENABLE_MODULES = YES;")
    A("CLANG_ENABLE_OBJC_ARC = YES;")
    A("COPY_PHASE_STRIP = NO;")
    if debug:
        A("DEBUG_INFORMATION_FORMAT = dwarf;")
        A("GCC_OPTIMIZATION_LEVEL = 0;")
        A("GCC_PREPROCESSOR_DEFINITIONS = (")
        A("\"DEBUG=1\",")
        A("\"$(inherited)\",")
        A(");")
        A("MTL_ENABLE_DEBUG_INFO = INCLUDE_SOURCE;")
        A("ONLY_ACTIVE_ARCH = YES;")
        A("SWIFT_ACTIVE_COMPILATION_CONDITIONS = DEBUG;")
        A("SWIFT_OPTIMIZATION_LEVEL = \"-Onone\";")
    else:
        A("DEBUG_INFORMATION_FORMAT = \"dwarf-with-dsym\";")
        A("ENABLE_NS_ASSERTIONS = NO;")
        A("MTL_ENABLE_DEBUG_INFO = NO;")
        A("SWIFT_OPTIMIZATION_LEVEL = \"-O\";")
    A("ENABLE_STRICT_OBJC_MSGSEND = YES;")
    A("GCC_C_LANGUAGE_STANDARD = gnu17;")
    A("GCC_NO_COMMON_BLOCKS = YES;")
    A("MACOSX_DEPLOYMENT_TARGET = 14.0;")
    A("SDKROOT = macosx;")
    A("};")
    A(f"name = {name};")
    A("};")

def target_config(cid, name):
    A(f"{cid} /* {name} */ = {{")
    A("isa = XCBuildConfiguration;")
    A("buildSettings = {")
    A("ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;")
    A("CODE_SIGN_STYLE = Automatic;")
    A("CURRENT_PROJECT_VERSION = 1;")
    A("ENABLE_HARDENED_RUNTIME = YES;")
    A("GENERATE_INFOPLIST_FILE = YES;")
    A("INFOPLIST_KEY_CFBundleDisplayName = LifeOS;")
    A("INFOPLIST_KEY_LSApplicationCategoryType = \"public.app-category.productivity\";")
    A("INFOPLIST_KEY_NSHumanReadableCopyright = \"Copyright © 2026 AUTOGIO\";")
    A("LD_RUNPATH_SEARCH_PATHS = (")
    A("\"$(inherited)\",")
    A("\"@executable_path/../Frameworks\",")
    A(");")
    A("MACOSX_DEPLOYMENT_TARGET = 14.0;")
    A("MARKETING_VERSION = 1.0.0;")
    A("PRODUCT_BUNDLE_IDENTIFIER = com.autogio.lifeos;")
    A("PRODUCT_NAME = \"$(TARGET_NAME)\";")
    A("SDKROOT = macosx;")
    A("SUPPORTED_PLATFORMS = macosx;")
    A("SWIFT_EMIT_LOC_STRINGS = YES;")
    A("SWIFT_VERSION = 5.0;")
    A("};")
    A(f"name = {name};")
    A("};")

proj_config(DBG_PROJ, "Debug", True)
proj_config(REL_PROJ, "Release", False)
target_config(DBG_TGT, "Debug")
target_config(REL_TGT, "Release")
A("/* End XCBuildConfiguration section */")
A("")
A("/* Begin XCConfigurationList section */")
A(f"{CONFLIST_TARGET} /* Build configuration list for PBXNativeTarget \"LifeOS\" */ = {{")
A("isa = XCConfigurationList;")
A("buildConfigurations = (")
A(f"{DBG_TGT} /* Debug */,")
A(f"{REL_TGT} /* Release */,")
A(");")
A("defaultConfigurationIsVisible = 0;")
A("defaultConfigurationName = Release;")
A("};")
A(f"{CONFLIST_PROJ} /* Build configuration list for PBXProject \"LifeOS\" */ = {{")
A("isa = XCConfigurationList;")
A("buildConfigurations = (")
A(f"{DBG_PROJ} /* Debug */,")
A(f"{REL_PROJ} /* Release */,")
A(");")
A("defaultConfigurationIsVisible = 0;")
A("defaultConfigurationName = Release;")
A("};")
A("/* End XCConfigurationList section */")
A("};")
A(f"rootObject = {PROJECT} /* Project object */;")
A("}")

out = "\n".join(lines) + "\n"
target = os.environ.get("PBXPROJ_OUT", "project.pbxproj")
open(target, "w").write(out)
print(f"Wrote {target}: {len(out)} bytes, {len(build_files)} build files, {len(file_refs)} refs")
