#include "tagmap.h"
#include <cassert>
#include <iostream>

void test_basic_operations() {
  Tagmap<std::string, std::string> tm;

  // Test insertion with Object
  Object<std::string, std::string> obj1("data1", {"tag1", "tag2"});
  tm.insert(obj1);
  assert(tm.listdata().size() == 1);
  assert(**tm.listdata().begin() == obj1.data);

  // Test insertion with data and tags
  tm.insert("data2", {"tag2", "tag3"});
  assert(tm.listdata().size() == 2);

  // Test tag retrieval
  auto tags = tm.listtags();
  assert(tags.size() == 3);
  assert(std::find(tags.begin(), tags.end(), "tag1") != tags.end());
  assert(std::find(tags.begin(), tags.end(), "tag2") != tags.end());
  assert(std::find(tags.begin(), tags.end(), "tag3") != tags.end());

  // Test find
  auto found = tm.find({"tag2"});
  assert(found.size() == 2);
}

void test_collision_handling() {
  Tagmap<int, std::string> tm;
  Object<int, std::string> obj1(1, {"tag1"});
  Object<int, std::string> obj2(1, {"tag2"});
  tm.insert(obj1);
  tm.insert(obj2);
  assert(tm.listdata().size() == 1); // Should handle same data with different tags
}

void test_empty_references() {
  Tagmap<std::string, std::string> tm;
  Object<std::string, std::string> obj("data", {});
  tm.insert(obj);
  assert(tm.listdata().size() == 0); // Should not store objects with empty references

  tm.insert("data2", {"tag"});
  tm.insert(Object<std::string, std::string>("data2", {}));
  assert(tm.listdata().size() == 0); // Replacing with empty references should remove
}

void test_erase() {
  Tagmap<std::string, std::string> tm;
  Object<std::string, std::string> obj("data", {"tag1", "tag2"});
  tm.insert(obj);

  // Erase by object
  auto erased = tm.erase(&obj);
  assert(erased.data == "data");
  assert(tm.listdata().size() == 0);

  // Erase by data
  tm.insert(obj);
  std::string obj_data = "data"; // Keep data alive for pointer
  auto erased_data = tm.erase(&obj_data);
  assert(erased_data == "data");
  assert(tm.listdata().size() == 0);

  // Erase by tags
  tm.insert(obj);
  auto erased_set = tm.erase({"tag1"});
  assert(erased_set.size() == 1);
  assert(*erased_set.begin() == "data");
}

void test_edge_cases() {
  Tagmap<std::string, std::string> tm;

  // Empty tagmap
  assert(tm.listdata().empty());
  assert(tm.listtags().empty());
  assert(tm.find({"nonexistent"}).empty());

  // Multiple objects with same tags
  tm.insert("data1", {"tag"});
  tm.insert("data2", {"tag"});
  auto found = tm.find({"tag"});
  assert(found.size() == 2);
}

void test_dangling_pointers() {
  Tagmap<std::string, std::string> tm;
  Object<std::string, std::string> obj("data", {"tag"});
  tm.insert(obj);
  auto ptrs = tm.listdata();
  tm.erase(&obj);
  // Note: Can't safely test *ptrs.begin() as it's undefined behavior
  // This just ensures no crash
}

int main() {
  test_basic_operations();
  test_collision_handling();
  test_empty_references();
  test_erase();
  test_edge_cases();
  test_dangling_pointers();

  std::cout << "All tests passed!" << std::endl;
  return 0;
}
