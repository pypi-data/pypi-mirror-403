#include "tagmap.h"
#include <cassert>
#include <chrono>
#include <iostream>
#include <random>
#include <string>

using namespace std::chrono;

// Random number generation utilities
std::random_device rd;
std::mt19937 gen(rd());
std::uniform_int_distribution<> dis(1, 1000);
std::uniform_int_distribution<> tag_dis(1, 50);

// Generate random string
std::string random_string(size_t length) {
    static const char alphanum[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    std::uniform_int_distribution<> char_dis(0, sizeof(alphanum) - 2);
    std::string s;
    s.reserve(length);
    for (size_t i = 0; i < length; ++i) s += alphanum[char_dis(gen)];
    return s;
}

// Generate random tags
std::unordered_set<std::string> random_tags(size_t count) {
    std::unordered_set<std::string> tags;
    while (tags.size() < count) tags.insert("tag" + std::to_string(tag_dis(gen)));
    return tags;
}

void stress_test() {
    Tagmap<std::string, std::string> tm;
    const size_t NUM_OBJECTS = 100000;   // 100,000 objects
    const size_t NUM_OPERATIONS = 10000; // 10,000 operations each
    std::vector<Object<std::string, std::string>> objects;

    // 1. Insert many objects
    auto start = high_resolution_clock::now();
    objects.reserve(NUM_OBJECTS);
    for (size_t i = 0; i < NUM_OBJECTS; ++i) {
      std::string data = "data" + std::to_string(i) + "_" + random_string(10);
      auto tags = random_tags(dis(gen) % 5 + 1); // 1-5 tags per object
      Object<std::string, std::string> obj(data, tags);
      objects.push_back(obj);
      tm.insert(obj); // Using Object insert
    }
    auto end = high_resolution_clock::now();
    auto duration = duration_cast<milliseconds>(end - start);
    std::cout << "Inserted " << NUM_OBJECTS << " objects in " << duration.count() << " ms\n";
    assert(tm.listdata().size() == NUM_OBJECTS);

    // 2. Stress test find operations
    start = high_resolution_clock::now();
    for (size_t i = 0; i < NUM_OPERATIONS; ++i) {
      size_t tag_count = dis(gen) % 5 + 1;
      auto search_tags = random_tags(tag_count);
      auto results = tm.find(search_tags);
      assert(results.size() <= NUM_OBJECTS); // Sanity check
    }
    end = high_resolution_clock::now();
    duration = duration_cast<milliseconds>(end - start);
    std::cout << "Performed " << NUM_OPERATIONS << " find operations in " << duration.count() << " ms\n";

    // 3. Stress test erase by object
    start = high_resolution_clock::now();
    size_t initial_size = tm.listdata().size();
    for (size_t i = 0; i < NUM_OPERATIONS && i < objects.size(); ++i) tm.erase(&objects[i]);
    end = high_resolution_clock::now();
    duration = duration_cast<milliseconds>(end - start);
    std::cout << "Erased " << std::min(NUM_OPERATIONS, objects.size()) << " objects by pointer in " << duration.count() << " ms\n";
    assert(tm.listdata().size() == initial_size - std::min(NUM_OPERATIONS, objects.size()));

    // Re-insert for next tests
    for (size_t i = 0; i < std::min(NUM_OPERATIONS, objects.size()); ++i) tm.insert(objects[i]);

    // 4. Stress test erase by data
    start = high_resolution_clock::now();
    initial_size = tm.listdata().size();
    for (size_t i = 0; i < NUM_OPERATIONS && i < objects.size(); ++i) tm.erase(&objects[i].data);
    end = high_resolution_clock::now();
    duration = duration_cast<milliseconds>(end - start);
    std::cout << "Erased " << std::min(NUM_OPERATIONS, objects.size()) << " objects by data in " << duration.count() << " ms\n";
    assert(tm.listdata().size() == initial_size - std::min(NUM_OPERATIONS, objects.size()));

    // Re-insert for next test
    for (size_t i = 0; i < std::min(NUM_OPERATIONS, objects.size()); ++i) tm.insert(objects[i]);

    // 5. Stress test erase by tags
    start = high_resolution_clock::now();
    initial_size = tm.listdata().size();
    for (size_t i = 0; i < NUM_OPERATIONS; ++i) {
      auto erase_tags = random_tags(dis(gen) % 5 + 1);
      auto erased = tm.erase(erase_tags);
      assert(erased.size() <= initial_size); // Can't erase more than we have
    }
    end = high_resolution_clock::now();
    duration = duration_cast<milliseconds>(end - start);
    std::cout << "Performed " << NUM_OPERATIONS << " erase-by-tags operations in " << duration.count() << " ms\n";

    // Final size check
    std::cout << "Final Tagmap size: " << tm.listdata().size() << "\n";
}

int main() {
  std::cout << "Starting stress test...\n";
  stress_test();
  std::cout << "Stress test completed successfully!\n";
  return 0;
}
