#pragma once

#include "lumyn/util/RefCounted.h"

namespace lumyn::internal
{
  template <typename T>
  class IntrusiveSharedPtr
  {
  public:
    IntrusiveSharedPtr(T *ptr = nullptr) : _ptr(ptr)
    {
      if (_ptr)
        _ptr->ref();
    }

    // Adopt a raw pointer without incrementing the refcount (use when a ref was
    // already taken on your behalf, e.g. items dequeued from FreeRTOS queues).
    struct AdoptTag {};
    static IntrusiveSharedPtr adopt(T *ptr) { return IntrusiveSharedPtr(ptr, AdoptTag{}); }

    ~IntrusiveSharedPtr()
    {
      if (_ptr)
        _ptr->unref();
    }

    IntrusiveSharedPtr(const IntrusiveSharedPtr &other) : _ptr(other._ptr)
    {
      if (_ptr)
        _ptr->ref();
    }

    IntrusiveSharedPtr &operator=(const IntrusiveSharedPtr &other)
    {
      if (this != &other)
      {
        if (_ptr)
          _ptr->unref();
        _ptr = other._ptr;
        if (_ptr)
          _ptr->ref();
      }
      return *this;
    }

    IntrusiveSharedPtr(IntrusiveSharedPtr &&other) noexcept : _ptr(other._ptr)
    {
      other._ptr = nullptr;
    }

    IntrusiveSharedPtr &operator=(IntrusiveSharedPtr &&other) noexcept
    {
      if (this != &other)
      {
        if (_ptr)
          _ptr->unref();
        _ptr = other._ptr;
        other._ptr = nullptr;
      }
      
      return *this;
    }

    T *get() const { return _ptr; }
    T &operator*() const { return *_ptr; }
    T *operator->() const { return _ptr; }
    explicit operator bool() const { return _ptr != nullptr; }

  private:
    // Private adopt constructor
    IntrusiveSharedPtr(T *ptr, AdoptTag) : _ptr(ptr) {}
    T *_ptr;
  };
}