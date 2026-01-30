#ifndef metkit_version_h
#define metkit_version_h

#define metkit_VERSION_STR "1.16.0"
#define metkit_VERSION     "1.16.0"

#define metkit_VERSION_MAJOR 1
#define metkit_VERSION_MINOR 16
#define metkit_VERSION_PATCH 0

#define metkit_GIT_SHA1 "f104efea40d66180a4c57f092ab5836d2f9dd084"

#ifdef __cplusplus
extern "C" {
#endif

const char * metkit_version();

unsigned int metkit_version_int();

const char * metkit_version_str();

const char * metkit_git_sha1();

#ifdef __cplusplus
}
#endif


#endif // metkit_version_h
