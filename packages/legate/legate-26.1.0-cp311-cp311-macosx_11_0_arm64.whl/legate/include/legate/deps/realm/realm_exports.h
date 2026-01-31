
#ifndef REALM_EXPORT_H
#define REALM_EXPORT_H

#ifdef REALM_STATIC_DEFINE
#  define REALM_EXPORT
#  define REALM_NO_EXPORT
#else
#  ifndef REALM_EXPORT
#    ifdef Realm_EXPORTS
        /* We are building this library */
#      define REALM_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define REALM_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef REALM_NO_EXPORT
#    define REALM_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef REALM_DEPRECATED
#  define REALM_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef REALM_DEPRECATED_EXPORT
#  define REALM_DEPRECATED_EXPORT REALM_EXPORT REALM_DEPRECATED
#endif

#ifndef REALM_DEPRECATED_NO_EXPORT
#  define REALM_DEPRECATED_NO_EXPORT REALM_NO_EXPORT REALM_DEPRECATED
#endif

/* NOLINTNEXTLINE(readability-avoid-unconditional-preprocessor-if) */
#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef REALM_NO_DEPRECATED
#    define REALM_NO_DEPRECATED
#  endif
#endif

#endif /* REALM_EXPORT_H */
