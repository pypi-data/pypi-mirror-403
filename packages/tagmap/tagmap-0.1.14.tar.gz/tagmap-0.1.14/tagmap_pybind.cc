#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "tagmap/tagmap.h"

#include <optional>
#include <string>
#include <unordered_set>

namespace py = pybind11;

using Tag = std::string;
using Data = std::string;
using Obj = Object<Data, Tag>;
using Map = Tagmap<Data, Tag>;

using ObjectsMap = decltype(std::declval<Map &>().objects);

static inline std::unordered_set<Tag> to_tagset(const py::handle &tags) {
  std::unordered_set<Tag> out;
  try {
    const auto n = py::len(tags);
    if (n > 0)
      out.reserve(static_cast<size_t>(n));
  } catch (const py::error_already_set &) {
    PyErr_Clear();
  }
  for (py::handle h : py::iter(tags))
    out.emplace(py::cast<Tag>(h));
  return out;
}

static inline ObjectsMap::iterator find_obj_it(Map &m, const Data &d) {
  Obj probe(d);
  const size_t key = m.getkey(probe);
  return m.objects.find(key);
}

static inline ObjectsMap::const_iterator find_obj_it(const Map &m,
                                                     const Data &d) {
  Obj probe(d);
  const size_t key = m.getkey(probe);
  return m.objects.find(key);
}

static inline bool has_data(const Map &m, const Data &d) {
  return find_obj_it(m, d) != m.objects.end();
}

static inline const Obj &get_obj_or_throw(const Map &m, const Data &d) {
  auto it = find_obj_it(m, d);
  if (it == m.objects.end())
    throw py::key_error("key not found: " + d);
  return it->second;
}

static inline void set_tags(Map &m, const Data &d,
                            const std::unordered_set<Tag> &tags) {
  m.insert(d, tags);
}

static inline std::optional<Obj> erase_data_if_exists(Map &m, const Data &d) {
  auto it = find_obj_it(m, d);
  if (it == m.objects.end())
    return std::nullopt;
  Obj removed = m.erase(&it->second);
  return removed;
}

static inline Obj erase_data_or_throw(Map &m, const Data &d) {
  auto it = find_obj_it(m, d);
  if (it == m.objects.end())
    throw py::key_error("key not found: " + d);
  return m.erase(&it->second);
}

static inline py::list keys_list(const Map &m) {
  py::list out(m.objects.size());
  size_t i = 0;
  for (const auto &kv : m.objects)
    out[i++] = py::cast(kv.second.data);
  return out;
}

static inline py::list values_list(const Map &m) {
  py::list out(m.objects.size());
  size_t i = 0;
  for (const auto &kv : m.objects)
    out[i++] = py::cast(kv.second.references);
  return out;
}

static inline py::list items_list(const Map &m) {
  py::list out(m.objects.size());
  size_t i = 0;
  for (const auto &kv : m.objects) {
    out[i++] = py::make_tuple(py::cast(kv.second.data),
                              py::cast(kv.second.references));
  }
  return out;
}

static inline std::vector<Tag> all_tags_vec(const Map &m) {
  return m.listtags();
}

static inline py::set query_all_of_py(const Map &m,
                                      const std::unordered_set<Tag> &tags) {
  py::set out;
  if (tags.empty()) {
    for (const auto &kv : m.objects)
      out.add(py::cast(kv.second.data));
    return out;
  }
  const auto ptrs = m.find(tags); // unordered_set<const Data*>
  for (const Data *p : ptrs)
    out.add(py::cast(*p));
  return out;
}

static inline py::set query_any_of_py(const Map &m,
                                      const std::unordered_set<Tag> &tags) {
  py::set out;
  if (tags.empty()) {
    for (const auto &kv : m.objects)
      out.add(py::cast(kv.second.data));
    return out;
  }

  std::unordered_set<size_t> keys;
  keys.reserve(tags.size());

  for (const auto &t : tags) {
    auto it = m.references.find(t);
    if (it == m.references.end())
      continue;
    keys.insert(it->second.begin(), it->second.end());
  }

  for (const size_t k : keys) {
    auto it = m.objects.find(k);
    if (it != m.objects.end())
      out.add(py::cast(it->second.data));
  }
  return out;
}

static inline size_t count_all_of(const Map &m,
                                  const std::unordered_set<Tag> &tags) {
  if (tags.empty())
    return m.objects.size();
  return m.find(tags).size();
}

static inline size_t count_any_of(const Map &m,
                                  const std::unordered_set<Tag> &tags) {
  if (tags.empty())
    return m.objects.size();
  std::unordered_set<size_t> keys;
  keys.reserve(tags.size());
  for (const auto &t : tags) {
    auto it = m.references.find(t);
    if (it == m.references.end())
      continue;
    keys.insert(it->second.begin(), it->second.end());
  }
  return keys.size();
}

static inline std::unordered_set<Tag> tags_of_or_empty(const Map &m,
                                                       const Data &d) {
  auto it = find_obj_it(m, d);
  if (it == m.objects.end())
    return {};
  return it->second.references;
}

static inline void add_tags(Map &m, const Data &d,
                            const std::unordered_set<Tag> &more) {
  auto cur = tags_of_or_empty(m, d);
  cur.insert(more.begin(), more.end());
  set_tags(m, d, cur);
}

static inline bool has_tag(const Map &m, const Data &d, const Tag &t) {
  auto it = find_obj_it(m, d);
  if (it == m.objects.end())
    return false;
  return it->second.references.find(t) != it->second.references.end();
}

static inline void remove_tag_or_throw(Map &m, const Data &d, const Tag &t) {
  auto it = find_obj_it(m, d);
  if (it == m.objects.end())
    throw py::key_error("key not found: " + d);
  auto tags = it->second.references;
  auto tit = tags.find(t);
  if (tit == tags.end())
    throw py::key_error("tag not found: " + t);
  tags.erase(tit);
  set_tags(m, d, tags);
}

static inline void discard_tag(Map &m, const Data &d, const Tag &t) {
  auto it = find_obj_it(m, d);
  if (it == m.objects.end())
    return;
  auto tags = it->second.references;
  auto tit = tags.find(t);
  if (tit == tags.end())
    return;
  tags.erase(tit);
  set_tags(m, d, tags);
}

static inline Map map_from_dict(const py::dict &d) {
  Map out;
  for (auto item : d) {
    Data data = py::cast<Data>(item.first);
    set_tags(out, data, to_tagset(item.second));
  }
  return out;
}

static inline Map map_from_keys_values(const py::iterable &keys,
                                       const py::iterable &values) {
  Map out;
  auto k_it = keys.begin();
  auto v_it = values.begin();
  while (k_it != keys.end() && v_it != values.end()) {
    Data data = py::cast<Data>(*k_it);
    set_tags(out, data, to_tagset(*v_it));
    ++k_it;
    ++v_it;
  }
  if (k_it != keys.end() || v_it != values.end())
    throw py::value_error("keys and values must have equal length");
  return out;
}

static inline Map map_from_pairs(const py::iterable &pairs) {
  Map out;
  for (py::handle h : pairs) {
    if (!py::isinstance<py::tuple>(h))
      throw py::type_error("each item must be a (key, tags) tuple");
    py::tuple t = py::reinterpret_borrow<py::tuple>(h);

    // Tests expect TypeError for malformed (non-2) tuples
    if (py::len(t) != 2)
      throw py::type_error("each item must be a (key, tags) pair");

    Data data = py::cast<Data>(t[0]);
    set_tags(out, data, to_tagset(t[1]));
  }
  return out;
}

PYBIND11_MODULE(tagmap, m) {
  m.doc() = "tagmap: fast tagged object map (pybind interface)";

  py::class_<Obj>(m, "Object")
      .def(py::init<>())
      .def(py::init<const Data &, const std::unordered_set<Tag> &>(),
           py::arg("data"), py::arg("tags"))
      .def_readwrite("data", &Obj::data)
      .def_readwrite("tags", &Obj::references);

  py::class_<Map>(m, "TagMap")
      .def(py::init<>())

      // Initializers
      .def(py::init([](const py::dict &d) { return map_from_dict(d); }),
           py::arg("d"))
      .def(py::init([](const py::iterable &keys, const py::iterable &values) {
             return map_from_keys_values(keys, values);
           }),
           py::arg("keys"), py::arg("values"))
      .def(py::init(
               [](const py::iterable &pairs) { return map_from_pairs(pairs); }),
           py::arg("items"))

      .def_static(
          "from_keys_values",
          [](const py::iterable &keys, const py::iterable &values) {
            return map_from_keys_values(keys, values);
          },
          py::arg("keys"), py::arg("values"))
      .def_static(
          "from_dict", [](const py::dict &d) { return map_from_dict(d); },
          py::arg("d"))

      .def("__len__", [](const Map &self) { return self.objects.size(); })
      .def("__bool__", [](const Map &self) { return !self.objects.empty(); })
      .def(
          "__contains__",
          [](const Map &self, const Data &k) { return has_data(self, k); },
          py::arg("key"))
      .def("__iter__",
           [](const Map &self) { return py::iter(keys_list(self)); })

      .def(
          "__getitem__",
          [](const Map &self, const Data &k) {
            return get_obj_or_throw(self, k).references;
          },
          py::arg("key"))
      .def(
          "__setitem__",
          [](Map &self, const Data &k, const py::iterable &tags) {
            set_tags(self, k, to_tagset(tags));
          },
          py::arg("key"), py::arg("tags"))
      .def(
          "__delitem__",
          [](Map &self, const Data &k) { (void)erase_data_or_throw(self, k); },
          py::arg("key"))

      .def("clear",
           [](Map &self) {
             self.objects.clear();
             self.references.clear();
           })

      .def("keys", [](const Map &self) { return keys_list(self); })
      .def("values", [](const Map &self) { return values_list(self); })
      .def("items", [](const Map &self) { return items_list(self); })
      .def("tags", [](const Map &self) { return all_tags_vec(self); })

      .def("to_dict",
           [](const Map &self) {
             py::dict out;
             for (const auto &kv : self.objects)
               out[py::cast(kv.second.data)] = py::cast(kv.second.references);
             return out;
           })

      .def(
          "get",
          [](const Map &self, const Data &k,
             py::object default_value) -> py::object {
            auto it = find_obj_it(self, k);
            if (it == self.objects.end())
              return default_value;
            return py::cast(it->second.references);
          },
          py::arg("key"), py::arg("default") = py::none())

      .def(
          "setdefault",
          [](Map &self, const Data &k, const py::iterable &default_tags) {
            auto it = find_obj_it(self, k);
            if (it != self.objects.end())
              return it->second.references;
            auto tags = to_tagset(default_tags);
            set_tags(self, k, tags);
            return tags;
          },
          py::arg("key"), py::arg("default"))

      .def(
          "pop",
          [](Map &self, const Data &k, py::object default_value) -> py::object {
            auto removed = erase_data_if_exists(self, k);
            if (!removed.has_value())
              return default_value;
            return py::cast(removed->references);
          },
          py::arg("key"), py::arg("default") = py::none())

      .def("popitem",
           [](Map &self) {
             if (self.objects.empty())
               throw py::key_error("popitem(): TagMap is empty");
             auto it = self.objects.begin();
             Data k = it->second.data;
             Obj removed = self.erase(&it->second);
             return py::make_tuple(k, removed.references);
           })

      .def(
          "update",
          [](Map &self, const py::dict &d) {
            for (auto item : d) {
              Data key = py::cast<Data>(item.first);
              set_tags(self, key, to_tagset(item.second));
            }
          },
          py::arg("d"))

      .def(
          "add_tag",
          [](Map &self, const Data &k, const Tag &t) {
            add_tags(self, k, {t});
          },
          py::arg("key"), py::arg("tag"))
      .def(
          "add_tags",
          [](Map &self, const Data &k, const py::iterable &tags) {
            add_tags(self, k, to_tagset(tags));
          },
          py::arg("key"), py::arg("tags"))
      .def(
          "remove_tag",
          [](Map &self, const Data &k, const Tag &t) {
            remove_tag_or_throw(self, k, t);
          },
          py::arg("key"), py::arg("tag"))
      .def(
          "discard_tag",
          [](Map &self, const Data &k, const Tag &t) {
            discard_tag(self, k, t);
          },
          py::arg("key"), py::arg("tag"))
      .def(
          "has_tag",
          [](const Map &self, const Data &k, const Tag &t) {
            return has_tag(self, k, t);
          },
          py::arg("key"), py::arg("tag"))

      .def(
          "find",
          [](const Map &self, const py::iterable &tags) {
            return query_all_of_py(self, to_tagset(tags));
          },
          py::arg("tags"))
      .def("query",
           [](const Map &self, py::args tags) {
             std::unordered_set<Tag> tset;
             tset.reserve(static_cast<size_t>(tags.size()));
             for (py::handle h : tags)
               tset.insert(py::cast<Tag>(h));
             return query_all_of_py(self, tset);
           })
      .def(
          "find_any",
          [](const Map &self, const py::iterable &tags) {
            return query_any_of_py(self, to_tagset(tags));
          },
          py::arg("tags"))
      .def("query_any",
           [](const Map &self, py::args tags) {
             std::unordered_set<Tag> tset;
             tset.reserve(static_cast<size_t>(tags.size()));
             for (py::handle h : tags)
               tset.insert(py::cast<Tag>(h));
             return query_any_of_py(self, tset);
           })

      .def(
          "count",
          [](const Map &self, const py::iterable &tags) {
            return py::int_(count_all_of(self, to_tagset(tags)));
          },
          py::arg("tags"))
      .def(
          "count_any",
          [](const Map &self, const py::iterable &tags) {
            return py::int_(count_any_of(self, to_tagset(tags)));
          },
          py::arg("tags"))

      // retain_where: ALL-of semantics, returns KEPT keys
      .def(
          "retain_where",
          [](Map &self, const py::iterable &tags) {
            const auto tset = to_tagset(tags);
            if (tset.empty())
              return keys_list(self);

            const auto keep_objs =
                self.findobject(tset); // unordered_set<const Obj*>
            std::unordered_set<size_t> keep_keys;
            keep_keys.reserve(keep_objs.size());

            py::list kept(keep_objs.size());
            size_t i = 0;
            for (const Obj *p : keep_objs) {
              keep_keys.insert(self.getkey(*p));
              kept[i++] = py::cast(p->data);
            }

            std::vector<size_t> del;
            del.reserve(self.objects.size() > keep_keys.size()
                            ? (self.objects.size() - keep_keys.size())
                            : 0);

            for (const auto &kv : self.objects) {
              if (!keep_keys.contains(kv.first))
                del.push_back(kv.first);
            }

            for (size_t k : del) {
              auto it = self.objects.find(k);
              if (it != self.objects.end())
                self.erase(&it->second);
            }

            return kept;
          },
          py::arg("tags"))

      // retain_where_any: ANY-of semantics, returns KEPT keys
      .def(
          "retain_where_any",
          [](Map &self, const py::iterable &tags) {
            const auto tset = to_tagset(tags);
            if (tset.empty())
              return keys_list(self);

            // Build union of keys matching ANY tag
            std::unordered_set<size_t> keep_keys;
            keep_keys.reserve(tset.size());

            for (const auto &t : tset) {
              auto it = self.references.find(t);
              if (it == self.references.end())
                continue;
              keep_keys.insert(it->second.begin(), it->second.end());
            }

            py::list kept(keep_keys.size());
            size_t i = 0;
            for (size_t k : keep_keys) {
              auto it = self.objects.find(k);
              if (it != self.objects.end())
                kept[i++] = py::cast(it->second.data);
            }

            // If some keys were stale (shouldn't happen), shrink list
            if (i != keep_keys.size())
              kept = kept.attr("__getitem__")(py::slice(0, i, 1));

            std::vector<size_t> del;
            del.reserve(self.objects.size() > keep_keys.size()
                            ? (self.objects.size() - keep_keys.size())
                            : 0);

            for (const auto &kv : self.objects) {
              if (!keep_keys.contains(kv.first))
                del.push_back(kv.first);
            }

            for (size_t k : del) {
              auto it = self.objects.find(k);
              if (it != self.objects.end())
                self.erase(&it->second);
            }

            return kept;
          },
          py::arg("tags"))

      .def(
          "erase",
          [](Map &self, const Data &k) {
            return erase_data_or_throw(self, k).references;
          },
          py::arg("key"))
      .def(
          "discard",
          [](Map &self, const Data &k) {
            return erase_data_if_exists(self, k).has_value();
          },
          py::arg("key"))
      .def(
          "erase_where",
          [](Map &self, const py::iterable &tags) {
            return self.erase(to_tagset(tags));
          },
          py::arg("tags"));
}
