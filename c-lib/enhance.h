/*******************************************************************************
*                           C extension for vimiv
* simple add-on to enhance brightness and contrast of an image on the pixel
* scale.
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

/**********************************
*  Plain C function declarations  *
**********************************/
static inline U_CHAR clamp(float value);
static inline float enhance_brightness(float value, float factor);
static inline float enhance_contrast(float value, float factor);
static void enhance_bc_c(unsigned char* data, const int size, float brightness,
                         float contrast, char* updated_data);
