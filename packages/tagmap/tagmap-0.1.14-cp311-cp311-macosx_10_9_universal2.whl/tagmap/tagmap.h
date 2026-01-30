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
    std::unordered_map<U, std::unordered_set<size_t>> references;
    std::unordered_map<size_t, Object<T, U>> objects;

    size_t getkey(const Object<T, U> &obj) const {
        size_t key = std::hash<Object<T, U>>()(obj);
        auto it = objects.find(key);
        while(it != objects.end() && it->second.data != obj.data) {
            key = (0xD1B54A32D192ED03ULL + key * 0x9E3779B97F4A7C15ULL);
            it = objects.find(key);
        }
        return key;
    }
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
        for(const auto &it: objects) retval.insert(&(it.second));
        return retval;
    }
    void insert(const Object<T, U>& value) {
        const size_t key = getkey(value);
        const auto it = objects.find(key);
        if(it != objects.end()) {
            for(const U& reference: value.references - it->second.references) references[reference].insert(key);
            for(const U& reference: it->second.references - value.references) {
                references[reference].erase(key);
                if(references[reference].empty()) references.erase(reference);
            }
            if(value.references.empty()) objects.erase(key);
            else it->second = value;
        }
        else {
            if(!value.references.empty()) {
                objects.emplace(key, value);
                for(const U& reference: value.references) references[reference].insert(key);
            }
        }
    }
    void insert(const T& data, const std::unordered_set<U>& tags) {
        Object<T, U> object = Object<T, U>(data, tags);
        insert(object); 
    }
    [[nodiscard]] std::unordered_set<const Object<T, U>*> findobject(const std::unordered_set<U>& tags) const {
        if(tags.empty()) return std::unordered_set<const Object<T, U>*>();
        std::vector<const std::unordered_set<size_t> *> keysets;
        keysets.reserve(tags.size());
        const std::unordered_set<size_t> *miniset = nullptr;
        size_t minisize = std::numeric_limits<size_t>::max();
        for(const U& tag: tags) {
            const auto it = references.find(tag);
            if(it != references.end()) {
                keysets.push_back(&it->second);
                if(it->second.size() < minisize) {
                    minisize = it->second.size();
                    miniset = &it->second;
                }
            }
            else return std::unordered_set<const Object<T, U>*>();
        }
        std::unordered_set<size_t> keys(*miniset);
        for(const std::unordered_set<size_t> *keyset: keysets) if(keyset != miniset) intersect(keys, *keyset);
        std::unordered_set<const Object<T, U>*> retval;
        retval.reserve(keys.size());
        for(size_t key: keys) {
            auto it = objects.find(key);
            if(it != objects.end()) retval.insert(&it->second);
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
        const size_t key = getkey(*object);
        const auto it = objects.find(key);
        if(it != objects.end()) {
            for(const U &ref: it->second.references) if(references.find(ref) != references.end()) {
                references[ref].erase(key);
                if(references[ref].empty()) references.erase(ref);
            } 
            Object<T, U> retval = it->second;
            objects.erase(it);
            return retval;
        }
        else return Object<T, U>();
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
