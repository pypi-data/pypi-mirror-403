#ifndef __tagmap_h__
#define __tagmap_h__

#include <cstdlib>
#include <algorithm>
#include <limits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

template<class T> std::unordered_set<T> operator+(const std::unordered_set<T>& set1, const std::unordered_set<T>& set2) {
    std::unordered_set<T> retval(set1);
    retval.reserve(set1.size()+set2.size());
    retval.insert(set2.begin(), set2.end());
    return retval;
}

template<class T> std::unordered_set<T> operator-(const std::unordered_set<T>& set1, const std::unordered_set<T>& set2) {
    std::unordered_set<T> retval;
    retval.reserve(set1.size());
    for(const T& val: set1) if(!set2.contains(val)) retval.insert(val);
    return retval;
}

template<class T> void intersect(std::unordered_set<T>& set1, const std::unordered_set<T>& set2) {
    std::unordered_set<T> retval;
    if(set1.size() > set2.size()) {
        retval.reserve(set2.size());
        for(const T& val: set2) if(set1.contains(val)) retval.insert(val);
    }
    else {
        retval.reserve(set1.size());
        for(const T& val: set1) if(set2.contains(val)) retval.insert(val);
    }
    set1.swap(retval);
}

template<class T, class U> struct Object {
    T data;
    std::unordered_set<U> references;

    Object() = default;
    Object(const T& d) : data(d) {}
    Object(const T& d, const std::unordered_set<U>& refs) : data(d), references(refs) {}
    bool operator==(const Object& other) const { return data == other.data; }
    bool operator!=(const Object& other) const { return !(*this == other); }
};

namespace std {
    template<class T, class U> struct hash<Object<T, U>> {
        size_t operator()(const Object<T, U>& object) const {
            return std::hash<T>()(object.data);
        }
    };
}

template<class T, class U> struct Tagmap {
    std::unordered_map<U, std::unordered_set<Object<T, U>*>> references;
    std::unordered_map<T, Object<T, U>> objects;
    [[nodiscard]] std::unordered_set<const T*> listdata() const {
        std::unordered_set<const T*> retval;
        retval.reserve(objects.size());
        for(const auto &it: objects) retval.insert(&(it.second.data));
        return retval;
    }
    [[nodiscard]] std::vector<U> listtags() const {
        std::vector<U> retval(references.size());
        std::transform(references.begin(), references.end(), retval.begin(), [](const auto& it) { return it.first; });
        return retval;
    }
    [[nodiscard]] std::unordered_set<const Object<T, U>*> listobjects() const {
        std::unordered_set<const Object<T, U>*> retval;
        retval.reserve(objects.size());
        for(const auto &it: objects) retval.insert(&(it.second));
        return retval;
    }
    void insert(const Object<T, U>& value) {
        if(value.references.empty()) {
            erase(&value);
            return;
        }

        auto it = objects.find(value.data);
        if(it == objects.end()) {
            auto [ins, ok] = objects.emplace(value.data, value);
            Object<T, U>* ptr = &ins->second;
            for(const U& reference: value.references) references[reference].insert(ptr);
            return;
        }

        Object<T, U>* ptr = &it->second;
        auto &oldrefs = it->second.references;

        for(const U& reference: value.references) {
            if(!oldrefs.contains(reference)) references[reference].insert(ptr);
        }

        for(const U& reference: oldrefs) {
            if(!value.references.contains(reference)) {
                auto rit = references.find(reference);
                if(rit != references.end()) {
                    rit->second.erase(ptr);
                    if(rit->second.empty()) references.erase(rit);
                }
            }
        }

        it->second = value;
    }
    void insert(const T& data, const std::unordered_set<U>& tags) {
        Object<T, U> object = Object<T, U>(data, tags);
        insert(object); 
    }
    [[nodiscard]] std::unordered_set<const Object<T, U>*> findobject(const std::unordered_set<U>& tags) const {
        if(tags.empty()) return std::unordered_set<const Object<T, U>*>();
        const std::unordered_set<Object<T, U>*> *miniset = nullptr;
        size_t minisize = std::numeric_limits<size_t>::max();
        std::vector<const std::unordered_set<Object<T, U>*>*> keysets;
        keysets.reserve(tags.size());

        for(const U& tag: tags) {
            const auto it = references.find(tag);
            if(it == references.end()) return std::unordered_set<const Object<T, U>*>();
            keysets.push_back(&it->second);
            if(it->second.size() < minisize) {
                minisize = it->second.size();
                miniset = &it->second;
            }
        }

        std::unordered_set<const Object<T, U>*> retval;
        if(miniset == nullptr || miniset->empty()) return retval;
        retval.reserve(miniset->size());

        for(Object<T, U>* obj: *miniset) {
            bool ok = true;
            for(const auto* keyset: keysets) {
                if(keyset == miniset) continue;
                if(!keyset->contains(obj)) {
                    ok = false;
                    break;
                }
            }
            if(ok) retval.insert(obj);
        }
        return retval;
    }
    [[nodiscard]] std::unordered_set<const T*> find(const std::unordered_set<U>& tags) const {
        const std::unordered_set<const Object<T, U>*> objectset = findobject(tags);
        std::unordered_set<const T*> retval;
        retval.reserve(objectset.size());
        for(const Object<T, U>* obj: objectset) retval.insert(&obj->data);
        return retval;
    }
    Object<T, U> erase(const Object<T, U>* object) {
        const auto it = objects.find(object->data);
        if(it == objects.end()) return Object<T, U>();

        Object<T, U>* ptr = &it->second;
        for(const U& ref: it->second.references) {
            auto rit = references.find(ref);
            if(rit == references.end()) continue;
            rit->second.erase(ptr);
            if(rit->second.empty()) references.erase(rit);
        }

        Object<T, U> retval = it->second;
        objects.erase(it);
        return retval;
    }
    T erase(const T* data) { 
        const Object<T, U> object = Object<T, U>(*data);
        return erase(&object).data; 
    }
    std::unordered_set<T> erase(const std::unordered_set<U>& tags) {
        const std::unordered_set<const Object<T, U>*> objectset = findobject(tags);
        std::unordered_set<T> retval;
        retval.reserve(objectset.size());
        for(const Object<T, U>* obj: objectset) retval.insert(erase(obj).data);
        return retval;
    }
};

#endif
