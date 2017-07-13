/*******************************************************************************
*                           C extension for vimiv
* simple add-on to enhance brightness and contrast of an image on the pixel
* scale.
*******************************************************************************/

#include "definitions.h"

/**********************************
*  Plain C function declarations  *
**********************************/
static inline U_CHAR clamp(float value);
static inline float enhance_brightness(float value, float factor);
static inline float enhance_contrast(float value, float factor);
static void enhance_bc_c(U_CHAR* data, const int size, U_SHORT has_alpha,
                         float brightness, float contrast, char* updated_data);
