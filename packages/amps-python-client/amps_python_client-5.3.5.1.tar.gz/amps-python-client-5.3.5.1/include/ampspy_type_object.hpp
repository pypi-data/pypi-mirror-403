////////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2010-2025 60East Technologies Inc., All Rights Reserved.
//
// This computer software is owned by 60East Technologies Inc. and is
// protected by U.S. copyright laws and other laws and by international
// treaties.  This computer software is furnished by 60East Technologies
// Inc. pursuant to a written license agreement and may be used, copied,
// transmitted, and stored only in accordance with the terms of such
// license agreement and with the inclusion of the above copyright notice.
// This computer software or any other copies thereof may not be provided
// or otherwise made available to any other person.
//
// U.S. Government Restricted Rights.  This computer software: (a) was
// developed at private expense and is in all respects the proprietary
// information of 60East Technologies Inc.; (b) was not developed with
// government funds; (c) is a trade secret of 60East Technologies Inc.
// for all purposes of the Freedom of Information Act; and (d) is a
// commercial item and thus, pursuant to Section 12.212 of the Federal
// Acquisition Regulations (FAR) and DFAR Supplement Section 227.7202,
// Government's use, duplication or disclosure of the computer software
// is subject to the restrictions set forth by 60East Technologies Inc..
//
////////////////////////////////////////////////////////////////////////////
#pragma once

#include <Python.h>

#if defined(AMPS_SHARED) && defined(_WIN32)
  #ifdef AMPS_BUILD
    #ifndef AMPSDLL
      #define AMPSDLL __declspec(dllexport)
    #endif
    #define AMPSDLL_EXTERN extern __declspec(dllexport)
  #else
    #ifndef AMPSDLL
      #define AMPSDLL __declspec(dllimport)
    #endif
    #define AMPSDLL_EXTERN extern __declspec(dllimport)
  #endif
#else
  #ifndef AMPSDLL
    #define AMPSDLL
  #endif
  #define AMPSDLL_EXTERN extern
#endif

namespace ampspy
{
  // A Python 2.x/3.x wrapper for creating a new type object, using the "limited api"
  // in 3.x and using a static PyTypeObject in 2.x.

  class ampspy_type_object_impl;
  class AMPSDLL ampspy_type_object
  {
  public:
    ampspy_type_object(void);
    ~ampspy_type_object(void);

    ampspy_type_object(const ampspy_type_object&) = delete;
    ampspy_type_object& operator=(const ampspy_type_object&) = delete;

    // Finish creating the type
    ampspy_type_object& createType(void);
    // Register this type with the given module
    ampspy_type_object& registerType(const char*, PyObject*);

    // Return the type object ready to be added to a containing module/object.
    PyTypeObject* pPyTypeObject(void) const;
    PyObject* pPyObject(void) const;

    operator PyTypeObject* (void) const
    {
      return pPyTypeObject();
    }

    operator PyObject* (void) const
    {
      return pPyObject();
    }


    ampspy_type_object& setName(const char*);
    ampspy_type_object& setBase(const ampspy_type_object&);
    ampspy_type_object& setBasicSize(size_t);
    ampspy_type_object& setHaveGC(void);
    ampspy_type_object& setBaseType(void);

    ampspy_type_object& setConstructorFunction(void*);
    template <class T>
    ampspy_type_object& setConstructorFunction(T* function_)
    {
      return setConstructorFunction((void*)function_);
    }
    ampspy_type_object& setDestructorFunction(void*);
    template <class T>
    ampspy_type_object& setDestructorFunction(T* function_)
    {
      return setDestructorFunction((void*)function_);
    }
    ampspy_type_object& setCallFunction(void*);
    template <class T>
    ampspy_type_object& setCallFunction(T* function_)
    {
      return setCallFunction((void*)function_);
    }
    ampspy_type_object& setDoc(const char*);
    ampspy_type_object& setTraverseFunction(void*);
    template <class T>
    ampspy_type_object& setTraverseFunction(T* function_)
    {
      return setTraverseFunction((void*)function_);
    }
    ampspy_type_object& setClearFunction(void*);
    template <class T>
    ampspy_type_object& setClearFunction(T* function_)
    {
      return setClearFunction((void*)function_);
    }

    ampspy_type_object& setCompareFunction(void*);
    template <class T>
    ampspy_type_object& setCompareFunction(T* function_)
    {
      return setCompareFunction((void*)function_);
    }

    ampspy_type_object& setStrFunction(void*);
    template <class T>
    ampspy_type_object& setStrFunction(T* function_)
    {
      return setStrFunction((void*)function_);
    }

    ampspy_type_object& setReprFunction(void*);
    template <class T>
    ampspy_type_object& setReprFunction(T* function_)
    {
      return setReprFunction((void*)function_);
    }

    // Takes care of setting the Py_TPFLAGS_HAVE_RICHCOMPARE for you too.
    ampspy_type_object& setRichCompareFunction(void*);
    template <class T>
    ampspy_type_object& setRichCompareFunction(T* function_)
    {
      return setRichCompareFunction((void*)function_);
    }

    ampspy_type_object& setWeakListOffset(size_t);

    ampspy_type_object& setIterFunction(void*);
    template <class T>
    ampspy_type_object& setIterFunction(T* function_)
    {
      return setIterFunction((void*)function_);
    }

    ampspy_type_object& setIterNextFunction(void*);
    template <class T>
    ampspy_type_object& setIterNextFunction(T* function_)
    {
      return setIterNextFunction((void*)function_);
    }

    ampspy_type_object& addMethod(const char* name_,
                                  void*       function_,
                                  const char* doc_);

    template <class T>
    ampspy_type_object& addMethod(const char* name_,
                                  T*          function_,
                                  const char* doc_)
    {
      return addMethod(name_, (void*)function_, doc_);
    }

    ampspy_type_object& addStaticMethod(const char* name_,
                                        void*       function_,
                                        const char* doc_);

    template <class T>
    ampspy_type_object& addStaticMethod(const char* name_,
                                        T*          function_,
                                        const char* doc_)
    {
      return addStaticMethod(name_, (void*)function_, doc_);
    }

    ampspy_type_object& addKeywordMethod(const char* name_,
                                         void*       function_,
                                         const char* doc_);
    template <class T>
    ampspy_type_object& addKeywordMethod(const char* name_,
                                         T*          function_,
                                         const char* doc_)
    {
      return addKeywordMethod(name_, (void*)function_, doc_);
    }

    ampspy_type_object& notCopyable(void);
    // Read-only members
    ampspy_type_object& addMember(const char* name_,
                                  size_t      value_);
    ampspy_type_object& addMember(const char* name_,
                                  const char* value_);

    ampspy_type_object& addGetter(const char* name_,
                                  void*       function_,
                                  const char* doc_);
    ampspy_type_object& addGetterSetter(const char* name_,
                                        void*       getter_,
                                        void*       setter_,
                                        const char* getterDoc_,
                                        const char* setterDoc_);
    template <class T, class U>
    ampspy_type_object& addGetterSetter(const char* name_,
                                        T*          getter_,
                                        U*          setter_,
                                        const char* getterDoc_,
                                        const char* setterDoc_)
    {
      return addGetterSetter(name_, (void*)getter_, (void*) setter_,
                             getterDoc_, setterDoc_);
    }

    ampspy_type_object& addStatic(const char* name_, PyObject* value_);

    bool isInstanceOf(PyObject* pPyObject)
    {
      if (!pPyObject || !pPyObject->ob_type)
      {
        return false;
      }
      return pPyObject->ob_type == pPyTypeObject();
    }

  protected:
    ampspy_type_object_impl* _pImpl;
  }; // class ampspy_type_object
}

