/*******************************************************************************
*                           C extension for vimiv
* definitions usable for more modules.
*******************************************************************************/

/*****************************************
*  Alpha channel depends on endianness  *
*****************************************/
#if G_BYTE_ORDER == G_LITTLE_ENDIAN /* BGRA */

#define ALPHA_CHANNEL 3

#elif G_BYTE_ORDER == G_BIG_ENDIAN /* ARGB */

#define ALPHA_CHANNEL 0

#else /* PDP endianness: RABG */

#define ALPHA_CHANNEL 1

#endif

/*************
*  Typedefs  *
*************/
typedef unsigned short U_SHORT;
typedef unsigned char U_CHAR;
