/*******************************************************************************
*                           C extension for vimiv
* Simple add-on to enhance brightness and contrast of an image on the pixel
* scale.
*******************************************************************************/

#include <Python.h>

#include "enhance.h"

/*****************************
*  Generate python functions *
*****************************/

static PyObject *
enhance_bc(PyObject *self, PyObject *args)
{
    /* Receive arguments from python */
    PyObject *py_data;
    float brightness;
    float contrast;
    if (!PyArg_ParseTuple(args, "Off",
                          &py_data, &brightness, &contrast))
        return NULL;

    /* Convert python bytes to U_CHAR* for pixel data */
    if (!PyBytes_Check(py_data)) {
        PyErr_SetString(PyExc_TypeError, "Expected bytes");
        return NULL;
    }
    U_CHAR* data = (U_CHAR*) PyBytes_AsString(py_data);
    const int size = PyBytes_Size(py_data);

    /* Run the C function to enhance brightness and contrast */
    char *updated_data = malloc(size);
    enhance_bc_c(data, size, brightness, contrast, updated_data);

    /* Return python memoryview of updated data */
    return PyMemoryView_FromMemory(updated_data, size, PyBUF_WRITE);
}

/*****************************
*  Initialize python module  *
*****************************/

static PyMethodDef EnhanceMethods[] = {
    {"enhance_bc", enhance_bc, METH_VARARGS, "Enhance brightness and contrast"},
    {NULL, NULL, 0, NULL}  /* Sentinel */
};

static struct PyModuleDef enhance = {
    PyModuleDef_HEAD_INIT,
    "_image_enhance", /* Name */
    NULL,         /* Documentation */
    -1,           /* Keep state in global variables */
    EnhanceMethods
};

PyMODINIT_FUNC
PyInit__image_enhance(void)
{
    PyObject *m = PyModule_Create(&enhance);
    if (m == NULL)
        return NULL;
    return m;
}

/***************************************
*  Actual C functions doing the math  *
***************************************/

/* Make sure value stays between 0 and 255 */
static inline U_CHAR clamp(float value)
{
    if (value < 0)
        return 0;
    else if (value > 255)
        return 255;
    return (U_CHAR) value;
}

/* Enhance brightness by multiplying pixel value with factor */
static inline float enhance_brightness(float value, float factor)
{
    return value * factor;
}

/* Enhance contrast by finding the difference to the mean value of 127 and
   changing it by factor. This makes high values higher and low values lower
   keeping the mean. */
static inline float enhance_contrast(float value, float factor)
{
    float diff = (127 - value) * factor;
    return 127 - diff;
}

/* Return the ARGB content of one pixel at index in data. */
static inline void set_pixel_content(U_CHAR* data, int index, U_CHAR* content)
{
    for (U_SHORT i = 0; i < 4; i++)
        content[i] = data[index + i];
}

/* Read pixel data of specific size and enhance brightness and contrast
   according to the two functions above. Change the values in updated_data which
   is of type char* so one pixel is equal to one byte allowing to create a
   python memoryview obect directly from memory. */
void enhance_bc_c(U_CHAR* data, const int size, float brightness,
                  float contrast, char* updated_data)
{
    for (int pixel = 0; pixel < size; pixel++) {
        /* Skip alpha channel */
        if (pixel  % 4 != ALPHA_CHANNEL) {
            float value = (float) data[pixel];
            value = enhance_brightness(value, brightness);
            value = enhance_contrast(value, contrast);
            value = clamp(value);
            updated_data[pixel] = value;
        }
        else
            updated_data[pixel] = (U_CHAR) data[pixel];
    }
}
