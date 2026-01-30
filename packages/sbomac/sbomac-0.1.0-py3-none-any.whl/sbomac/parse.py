# Copyright (C) 2026 Anthony Harrison
# SPDX-License-Identifier: Apache-2.0

# Parse YAML file

import yaml
from lib4sbom.data.document import SBOMDocument
from lib4sbom.data.package import SBOMPackage
from lib4sbom.data.relationship import SBOMRelationship
from lib4sbom.data.service import SBOMService
from lib4sbom.generator import SBOMGenerator
from lib4sbom.output import SBOMOutput
from lib4sbom.sbom import SBOM


class SBOMascode:

    def __init__(self, name, debug=False):
        self.name = name
        self.elements = []
        self.debug = debug
        self.sbomtype = "design"
        self.author = None
        self.supplier = None
        self.email = ""

    def set_sbom_format(self, sbom_standard, sbom_format):
        self.sbom_standard = sbom_standard
        self.sbom_format = sbom_format

    def set_lifecycle(self, sbomtype):
        self.sbomtype = sbomtype

    def process_element(self, element_info, parent="-"):
        type_mapping = {
            "system": "device",
            "hardware": "device",
            "software": "application",
        }
        # print (dict(element_info))
        if self.debug:
            print(f"Element: {element_info['name']}. Parent {parent}")
            print(f"\tName: {element_info['name']}")
            print(f"\tType: {element_info['type']}")
            print(f"\tSummary: {element_info.get('summary','')}")
        element = {}
        element["name"] = element_info["name"].replace(" ", "-")
        if type_mapping.get(element_info["type"]) is not None:
            element["type"] = type_mapping.get(element_info["type"])
        else:
            element["type"] = element_info["type"]
        element["description"] = element_info.get("description", "")
        element["comment"] = element_info.get("comment", "")
        element["vendor"] = element_info.get("vendor", "")
        element["parent"] = parent.replace(" ", "-")
        self.elements.append(element)
        if "element" in element_info:
            for e in element_info["element"]:
                self.process_element(e, element_info["name"])

    def load(self, filename):
        # Load YAML file
        with open(filename, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if self.debug:
            print(data)
        for element in data["element"]:
            self.process_element(element)
        self.supplier = data.get("supplier")
        self.author = data.get("author")
        self.email = data.get("email")

    def generate(self, filename):
        application = self.name
        application_id = "CDXRef-DOCUMENT"
        relationships = []
        sbom_relationship = SBOMRelationship()
        sbom_relationship.initialise()
        sbom_relationship.set_relationship(application_id, "DESCRIBES", application)
        sbom_relationship.set_relationship_id(None, application_id)
        relationships.append(sbom_relationship.get_relationship())

        sbom_packages = {}
        sbom_services = {}
        ids = {}
        my_package = SBOMPackage()
        my_service = SBOMService()

        for index, element in enumerate(self.elements):
            sbom_relationship.initialise()
            if element["type"] == "service":
                my_service.initialise()
                my_service.set_name(element["name"])
                if "description" in element and len(element["description"]) > 0:
                    my_service.set_description(element["description"])
                if "vendor" in element:
                    my_service.set_provider(name=element["vendor"])
                if "comment" in element and len(element["comment"]) > 0:
                    my_package.set_comment(element["comment"])
                if "version" in element:
                    my_service.set_version(element["version"])
                    sbom_services[
                        (my_service.get_name(), my_service.get_value("version"))
                    ] = my_service.get_service()
                else:
                    my_service.set_id(f"{index+1}-{my_service.get_name()}")
                    sbom_services[(my_service.get_name(), "NOTDEFINED")] = (
                        my_service.get_service()
                    )
                if element["parent"] == "-":
                    sbom_relationship.set_relationship(
                        application, "DEPENDS_ON", my_service.get_value("name")
                    )
                    sbom_relationship.set_relationship_id(
                        application_id, my_service.get_value("id")
                    )
                else:
                    # Get id of parent
                    parent_id = ids[element["parent"]]
                    sbom_relationship.set_relationship(
                        element["parent"], "DEPENDS_ON", my_service.get_value("name")
                    )
                    sbom_relationship.set_relationship_id(
                        parent_id, my_service.get_value("id")
                    )
                ids[my_service.get_name()] = my_service.get_value("id")
            else:
                my_package.initialise()
                my_package.set_name(element["name"])
                my_package.set_type(element["type"])
                version_defined = False
                if "version" in element:
                    my_package.set_version(element["version"])
                    version_defined = True
                if "description" in element and len(element["description"]) > 0:
                    my_package.set_description(element["description"])
                if "vendor" in element:
                    my_package.set_supplier("Organization", element["vendor"])
                if "comment" in element and len(element["comment"]) > 0:
                    my_package.set_comment(element["comment"])
                if version_defined:
                    sbom_packages[
                        (my_package.get_name(), my_package.get_value("version"))
                    ] = my_package.get_package()
                else:
                    my_package.set_id(f"{index+1}-{my_package.get_name()}")
                    sbom_packages[(my_package.get_name(), "NOTDEFINED")] = (
                        my_package.get_package()
                    )
                if element["parent"] == "-":
                    sbom_relationship.set_relationship(
                        application, "DEPENDS_ON", my_package.get_value("name")
                    )
                    sbom_relationship.set_relationship_id(
                        application_id, my_package.get_value("id")
                    )
                else:
                    # Get id of parent
                    parent_id = ids[element["parent"]]
                    sbom_relationship.set_relationship(
                        element["parent"], "DEPENDS_ON", my_package.get_value("name")
                    )
                    sbom_relationship.set_relationship_id(
                        parent_id, my_package.get_value("id")
                    )
                ids[my_package.get_name()] = my_package.get_value("id")
            relationships.append(sbom_relationship.get_relationship())
        # Generate BOM
        my_sbom = SBOM()
        my_sbom.set_type(sbom_type=self.sbom_standard)
        # Latest version of standard
        my_sbom.set_version("1.7" if self.sbom_standard == "cyclonedx" else "2.3")
        my_doc = SBOMDocument()
        my_doc.set_value("lifecycle", self.sbomtype)
        my_doc.set_value("metadata_supplier", self.supplier)
        my_doc.set_creator("person", f"{self.author}#{self.email}")
        # Type of item (system)
        my_doc.set_metadata_type("device")
        # Assemble document
        my_sbom.add_document(my_doc.get_document())
        my_sbom.add_packages(sbom_packages)
        my_sbom.add_services(sbom_services)
        my_sbom.add_relationships(relationships)
        my_generator = SBOMGenerator(
            False, sbom_type=self.sbom_standard, format=self.sbom_format
        )
        my_generator.generate(application, my_sbom.get_sbom(), send_to_output=False)
        sbom_out = SBOMOutput(filename, output_format=self.sbom_format)
        sbom_out.generate_output(my_generator.get_sbom())


if __name__ == "__main__":
    sbom_file = "design.yaml"
    with open(sbom_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        # print (data)
    # Create SBOM
    sbom = SBOMascode("test")
    # Create metadata
    sbom.set_sbom_format("cyclonedx", "json")
    # set lifecycle to Design
    # Process each element
    for element in data["element"]:
        sbom.process_element(element)
    # Show relationships
    # Generate
    sbom.generate("")
