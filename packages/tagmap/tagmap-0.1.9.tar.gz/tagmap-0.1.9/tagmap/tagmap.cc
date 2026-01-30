#include <iostream>
#include "tagmap.h"

int main()
{
    Tagmap<std::string, std::string> tagmap;

    Object<std::string, std::string> obj1("Object1", {"tag1", "tag2"});
    Object<std::string, std::string> obj2("Object2", {"tag2", "tag3"});
    Object<std::string, std::string> obj3("Object3", {"tag3", "tag4"});

    tagmap.insert(obj1);
    tagmap.insert(obj2);
    tagmap.insert(obj3);

    std::cout<<"{objects}: {";
    for(const auto& obj: tagmap.listdata()) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{objects}: {";
    for(const auto& obj: tagmap.listobjects()) std::cout<<obj->data<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{tags}: {";
    for(const auto& obj: tagmap.listtags()) std::cout<<obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{tag1}: {";
    for(const auto& obj: tagmap.find({"tag1"})) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{tag2}: {";
    for(const auto& obj: tagmap.find({"tag2"})) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{tag3}: {";
    for(const auto& obj: tagmap.find({"tag3"})) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{tag2, tag3}: {";
    for(const auto& obj: tagmap.find({"tag2", "tag3"})) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"D{tag2, tag3}: {";
    for(const auto& obj: tagmap.erase({"tag2", "tag3"})) std::cout<<obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{objects}: {";
    for(const auto& obj: tagmap.listdata()) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{objects}: {";
    for(const auto& obj: tagmap.listobjects()) std::cout<<obj->data<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{tags}: {";
    for(const auto& obj: tagmap.listtags()) std::cout<<obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{tag1}: {";
    for(const auto& obj: tagmap.find({"tag1"})) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{tag2}: {";
    for(const auto& obj: tagmap.find({"tag2"})) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{tag3}: {";
    for(const auto& obj: tagmap.find({"tag3"})) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{tag2, tag3}: {";
    for(const auto& obj: tagmap.find({"tag2", "tag3"})) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"D{object3}: {";
    std::cout<<tagmap.erase(&obj3).data<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{objects}: {";
    for(const auto& obj: tagmap.listobjects()) std::cout<<obj->data<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{tags}: {";
    for(const auto& obj: tagmap.listtags()) std::cout<<obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{potato}: {";
    for(const auto& obj: tagmap.find({"potato"})) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    std::cout<<"{}: {";
    for(const auto& obj: tagmap.find({})) std::cout<<*obj<<", ";
    std::cout<<"}"<<std::endl;

    return EXIT_SUCCESS;
}

