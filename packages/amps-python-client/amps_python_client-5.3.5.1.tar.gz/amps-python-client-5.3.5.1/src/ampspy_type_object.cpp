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
#define PY_SSIZE_T_CLEAN 1

#include <Python.h>
#include <structmember.h>
#include <ampspy_type_object.hpp>
#include <vector>
#include <string>


namespace ampspy
{
  class ampspy_type_object_impl
  {
  public:
    ampspy_type_object_impl(void)
    {
#if PY_MAJOR_VERSION < 3
      memset(&_typeObject, 0, sizeof(PyTypeObject));
      PyTypeObject newObject =
      {
        PyVarObject_HEAD_INIT(NULL, 0)
      };
      _typeObject = newObject;
#else
      _pTypeObject = 0;
      memset(&_typeSpec, 0, sizeof(PyType_Spec));
      _weakListOffset = 0;
#endif
    }

#if PY_MAJOR_VERSION >= 3
    void addSlot(int slot_, void* value_)
    {
      PyType_Slot slot = { slot_, value_ };
      _slotList.push_back(slot);
    }
#endif

    void addMethod(const char* name_, void* function_, int flags_, const char* doc_)
    {
      PyMethodDef methodDef = { name_, (PyCFunction) function_, flags_, doc_ };
      _methodList.push_back(methodDef);
    }

    void addMember(const char* name_, size_t offset_)
    {
      PyMemberDef memberDef = { (char*) name_, T_PYSSIZET, (Py_ssize_t) offset_, READONLY };
      _memberList.push_back(memberDef);
    }

    void addGetter(const char* name_, void* function_, const char* doc_)
    {
      PyGetSetDef getSetDef = { (char*) name_, (getter)function_, NULL, (char*) doc_, NULL };
      _getterList.push_back(getSetDef);
    }

    void addGetterSetter(const char* name_, void* getter_, void* setter_,
                         const char* getterDoc_, const char* setterDoc_)
    {
      PyGetSetDef getSetDef = { (char*) name_, (getter)getter_, (setter)setter_, (char*)getterDoc_, (char*)setterDoc_ };
      _getterList.push_back(getSetDef);
    }

    void addStatic(const char* name_, PyObject* value_)
    {
#if PY_MAJOR_VERSION < 3
      // Add it right to the tp_dict of the type, which seems to be the standard way to do this
      // for non heap types in Python 2.x.
      PyDict_SetItemString(_typeObject.tp_dict, name_, value_);
#else
      // Since this is a heap type, we can use SetAttrString on it safely.
      PyObject_SetAttrString(pPyObject(), name_, value_);
#endif
    }

#if PY_MAJOR_VERSION >= 3
    void setupWeakListOffset(void)
    {
      // This code is a bit dangerous. PyTypeObject is opaque to us, but we need to set one of its members,
      // tp_weaklistoffset, as there's no other way to create a weakref compatible heap type until 3.9 using
      // the limited api.
      //
      // We're depending on something that's been true for over 20 years, that the tp_weaklistoffset is
      // located four void*'s after the tp_doc slot. The location of the tp_doc slot is unpredictable, but
      // once we find the tp_doc slot, we can advance 4 void*'s and then set that memory to the weak list offset.

      const size_t max_scan_slots = 32;
      const size_t tp_doc__to__tp_weaklistoffset__distance = 4; // in void*'s

      // First, find the value of the doc string.
      void* docString = PyType_GetSlot(_pTypeObject, Py_tp_doc);
      if (!docString || !_weakListOffset)
      {
        return;
      }

      // Now scan for that value in the type object.
      void** pMemory = (void**)(_pTypeObject);
      void** pMemoryEnd = pMemory + max_scan_slots;
      for (; pMemory != pMemoryEnd; ++pMemory)
      {
        if (*pMemory == docString)
        {
          // Found the tp_doc value.. Advance to tp_weaklistoffset, and make sure it is unset.
          pMemory += tp_doc__to__tp_weaklistoffset__distance;
          size_t* ptp_weaklistoffset = (size_t*) pMemory;
          if (!*ptp_weaklistoffset)
          {
            *ptp_weaklistoffset = _weakListOffset;
          }
          break;
        }
      }
    }
#endif

    void createType(void)
    {
      _methodList.emplace_back( PyMethodDef({ NULL }) );
      _memberList.emplace_back( PyMemberDef({ NULL }) );
      _getterList.emplace_back( PyGetSetDef({ NULL }) );
#if PY_MAJOR_VERSION < 3
      _typeObject.tp_new = PyType_GenericNew;
      _typeObject.tp_methods = _methodList.data();
      _typeObject.tp_members = _memberList.data();
      _typeObject.tp_getset  = _getterList.data();
      PyType_Ready(&_typeObject);
      Py_INCREF(&_typeObject);
#else
      assert(!_pTypeObject);
      addSlot(Py_tp_new, (void*)PyType_GenericNew);
      addSlot(Py_tp_methods, _methodList.data());
      addSlot(Py_tp_members, _memberList.data());
      addSlot(Py_tp_getset, _getterList.data());
      PyType_Slot slot = { 0, NULL };
      _slotList.push_back(slot);
      _typeSpec.slots = _slotList.data();
      _pTypeObject = (PyTypeObject*)PyType_FromSpec(&_typeSpec);
      if (_weakListOffset)
      {
        setupWeakListOffset();
      }
#endif
    }

    void registerType(const char* moduleEntryName_, PyObject* module_)
    {
      if (module_)
      {
        PyModule_AddObject(module_, moduleEntryName_, pPyObject());
      }
    }

    std::string              _name;
    std::vector<PyMethodDef> _methodList;
    std::vector<PyGetSetDef> _getterList;
    std::vector<PyMemberDef> _memberList;

#if PY_MAJOR_VERSION < 3
    PyTypeObject             _typeObject;
    PyObject* pPyObject(void)
    {
      return (PyObject*)(&_typeObject);
    }
    PyTypeObject* pPyTypeObject(void)
    {
      return &_typeObject;
    }
#else
    PyTypeObject*            _pTypeObject;
    PyType_Spec              _typeSpec;
    std::vector<PyType_Slot> _slotList;
    size_t                   _weakListOffset;
    PyObject* pPyObject(void)
    {
      return (PyObject*)_pTypeObject;
    }
    PyTypeObject* pPyTypeObject(void)
    {
      return _pTypeObject;
    }
#endif
  }; // ampspy_type_object_impl

  static PyObject* not_copyable(PyObject* self, PyObject* args)
  {
    PyErr_SetString(PyExc_TypeError, "This type cannot be copied.");
    return NULL;
  }

  ampspy_type_object::ampspy_type_object(void)
    : _pImpl(new ampspy_type_object_impl())
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_flags = Py_TPFLAGS_DEFAULT;
#else
    _pImpl->_typeSpec.flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HEAPTYPE;
#endif
  }

  ampspy_type_object::~ampspy_type_object(void)
  {
    delete _pImpl;
    _pImpl = 0;
  }
  ampspy_type_object& ampspy_type_object::createType(void)
  {
    _pImpl->createType();
    return *this;
  }

  // Finish creating the type and register it with the given module
  ampspy_type_object& ampspy_type_object::registerType(const char* name_,
                                                       PyObject* module_)
  {
    _pImpl->registerType(name_, module_);
    return *this;
  }

  // Return the type object ready to be added to the object.
  PyTypeObject* ampspy_type_object::pPyTypeObject(void) const
  {
    return _pImpl->pPyTypeObject();
  }

  // Return the type object ready to be added to the object.
  PyObject* ampspy_type_object::pPyObject(void) const
  {
    return _pImpl->pPyObject();
  }

  ampspy_type_object& ampspy_type_object::setName(const char* name_)
  {
    _pImpl->_name.assign(name_);
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_name = _pImpl->_name.data();
#else
    _pImpl->_typeSpec.name = _pImpl->_name.data();
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setBase(const ampspy_type_object& base_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_base = base_.pPyTypeObject();
#else
    _pImpl->addSlot(Py_tp_base, base_.pPyTypeObject());
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setBasicSize(size_t basicSize_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_basicsize = basicSize_;
#else
    _pImpl->_typeSpec.basicsize = (int)basicSize_;
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setHaveGC(void)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_flags |= Py_TPFLAGS_HAVE_GC;
#else
    _pImpl->_typeSpec.flags |= Py_TPFLAGS_HAVE_GC;
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setBaseType(void)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_flags |= Py_TPFLAGS_BASETYPE;
#else
    _pImpl->_typeSpec.flags |= Py_TPFLAGS_BASETYPE;
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setConstructorFunction(void* function_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_init = (initproc) function_;
#else
    _pImpl->addSlot(Py_tp_init, function_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setDestructorFunction(void* function_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_dealloc = (destructor) function_;
#else
    _pImpl->addSlot(Py_tp_dealloc, function_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setDoc(const char* doc_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_doc = doc_;
#else
    _pImpl->addSlot(Py_tp_doc, (void*) doc_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setTraverseFunction(void* function_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_traverse = (traverseproc) function_;
#else
    _pImpl->addSlot(Py_tp_traverse, function_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setClearFunction(void* function_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_clear = (inquiry) function_;
#else
    _pImpl->addSlot(Py_tp_clear, function_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setCallFunction(void* function_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_call = (ternaryfunc) function_;
#else
    _pImpl->addSlot(Py_tp_call, function_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setCompareFunction(void* function_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_compare = (cmpfunc) function_;
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setStrFunction(void* function_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_str = (reprfunc) function_;
#else
    _pImpl->addSlot(Py_tp_str, function_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setReprFunction(void* function_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_repr = (reprfunc) function_;
#else
    _pImpl->addSlot(Py_tp_repr, function_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setWeakListOffset(size_t weakListOffset_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_weaklistoffset = weakListOffset_;
#else
    _pImpl->_weakListOffset = weakListOffset_;
    _pImpl->addMember("__weakrefoffset__", weakListOffset_);
    _pImpl->addMember("__weaklistoffset__", weakListOffset_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setRichCompareFunction(void* function_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_richcompare = (richcmpfunc) function_;
    _pImpl->_typeObject.tp_flags |= Py_TPFLAGS_HAVE_RICHCOMPARE;
#else
    _pImpl->addSlot(Py_tp_richcompare, function_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setIterFunction(void* function_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_iter = (getiterfunc) function_;
#else
    _pImpl->addSlot(Py_tp_iter, function_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::setIterNextFunction(void* function_)
  {
#if PY_MAJOR_VERSION < 3
    _pImpl->_typeObject.tp_iternext = (iternextfunc) function_;
#else
    _pImpl->addSlot(Py_tp_iternext, function_);
#endif
    return *this;
  }

  ampspy_type_object& ampspy_type_object::addMethod(const char* name_,
                                                    void* function_,
                                                    const char* doc_)
  {
    _pImpl->addMethod(name_, function_, METH_VARARGS, doc_);
    return *this;
  }

  ampspy_type_object& ampspy_type_object::addStaticMethod(const char* name_,
                                                          void* function_,
                                                          const char* doc_)
  {
    _pImpl->addMethod(name_, function_, METH_VARARGS | METH_STATIC, doc_);
    return *this;
  }

  ampspy_type_object& ampspy_type_object::addKeywordMethod(const char* name_,
                                                           void* function_,
                                                           const char* doc_)
  {
    _pImpl->addMethod(name_, function_, METH_VARARGS | METH_KEYWORDS, doc_);
    return *this;
  }

  ampspy_type_object& ampspy_type_object::addGetter(const char* name_,
                                                    void* function_,
                                                    const char* doc_)
  {
    _pImpl->addGetter(name_, function_, doc_);
    return *this;
  }

  ampspy_type_object& ampspy_type_object::addGetterSetter(const char* name_,
                                                          void* getter_,
                                                          void* setter_,
                                                          const char* getterDoc_,
                                                          const char* setterDoc_)
  {
    _pImpl->addGetterSetter(name_, getter_, setter_, getterDoc_, setterDoc_);
    return *this;
  }

  ampspy_type_object& ampspy_type_object::addStatic(const char* name_,
                                                    PyObject* value_)
  {
    _pImpl->addStatic(name_, value_);
    return *this;
  }

  ampspy_type_object& ampspy_type_object::notCopyable(void)
  {
    _pImpl->addMethod("__copy__", (void*)not_copyable, METH_VARARGS,
                      "__copy__ not supported.");
    _pImpl->addMethod("__deepcopy__", (void*)not_copyable, METH_VARARGS,
                      "__deepcopy__ not supported.");
    return *this;
  }
}
