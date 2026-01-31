# Requirements import

import gzip
import json
import os
import re
import shutil
import sqlite3
import urllib.request
import warnings
import zipfile
from datetime import datetime

import gdown
import numpy as np
import pandas as pd
import pkg_resources
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .Enrichment import GetData, PathMetadata

# loading for test or inside library


pd.options.mode.chained_assignment = None
warnings.filterwarnings("ignore")


# Fucntions for data preparing


# Data downloading


class Donwload(PathMetadata):

    # ref_gene
    def download_ref(self):
        """
        This method downloads and returns combined human/rat/mice reference genome.

        Source: NCBI [https://www.ncbi.nlm.nih.gov/]

        Returns:
            dict (dict) - ref_genome
        """

        print("\n")
        print("REF-GENOME downloading...")

        gdown.download(
            "https://drive.google.com/uc?id=18B5NGrqrxkQXnx-FMi6RGBGC2zoRjrEW",
            os.path.join(self.path_tmp, "gene_dictionary_jbio.json"),
        )

        with open(
            os.path.join(self.path_tmp, "gene_dictionary_jbio.json"), "r"
        ) as json_file:
            gene_dictionary = json.load(json_file)

        os.remove(os.path.join(self.path_tmp, "gene_dictionary_jbio.json"))

        return gene_dictionary

    # ref_gene-RNA-SEQ
    def download_rns_seq(self):
        """
        This method downloads and returns the tissue-specific RNA-SEQ data including:
           -human_tissue_expression_HPA
           -human_tissue_expression_RNA_total_tissue
           -human_tissue_expression_fetal_development_circular

        Source: NCBI [https://www.ncbi.nlm.nih.gov/]

        Returns:
           dict (dict) - RNAseq data
        """

        print("\n")
        print("RNA-SEQ data downloading...")

        gdown.download(
            "https://drive.google.com/uc?id=17_cON3h4Tg9iaPaUSm0rrn__NuY7XlHL",
            os.path.join(self.path_tmp, "human_tissue_expression.json"),
        )

        with open(
            os.path.join(self.path_tmp, "human_tissue_expression.json"), "r"
        ) as json_file:
            rna_seq_list = json.load(json_file)

        os.remove(os.path.join(self.path_tmp, "human_tissue_expression.json"))

        return rna_seq_list

    # IntAct_download
    def download_IntAct(self):
        """
        This method downloads and returns IntAct data.

        Source: https://www.ebi.ac.uk/intact/home

        Returns:
            dict (dict) - IntAct data
        """

        print("\n")
        print("IntAct data downloading...")

        # Affinomics - Interactions curated for the Affinomics consortium

        try:
            print("\nAffinomics...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Affinomics.zip",
                os.path.join(self.path_tmp, "Affinomics.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Affinomics.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Affinomics.zip"))

        except:

            print("\nFailed - Affinomics downloading!")

        # Alzheimers - Interaction dataset based on proteins with an association to Alzheimer disease

        try:
            print("\nAlzheimers...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Alzheimers.zip",
                os.path.join(self.path_tmp, "Alzheimers.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Alzheimers.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Alzheimers.zip"))

        except:

            print("\nFailed - Alzheimers downloading!")

        # BioCreative - Critical Assessment of Information Extraction systems in Biology

        try:
            print("\nBioCreative...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/BioCreative.zip",
                os.path.join(self.path_tmp, "BioCreative.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "BioCreative.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "BioCreative.zip"))

        except:

            print("\nFailed - BioCreative downloading!")

        # Cancer - Interactions investigated in the context of cancer

        try:
            print("\nCancer...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Cancer.zip",
                os.path.join(self.path_tmp, "Cancer.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Cancer.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Cancer.zip"))

        except:

            print("\nFailed - Cancer downloading!")

        # Cardiac - Interactions involving cardiac related proteins

        try:
            print("\nCardiac...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Cardiac.zip",
                os.path.join(self.path_tmp, "Cardiac.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Cardiac.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Cardiac.zip"))

        except:

            print("\nFailed - Cardiac downloading!")

        # Chromatin - Epigenetic interactions resulting in chromatin modulation

        try:
            print("\nChromatin...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Chromatin.zip",
                os.path.join(self.path_tmp, "Chromatin.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Chromatin.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Chromatin.zip"))

        except:

            print("\nFailed - Chromatin downloading!")

        # Coronavirus - Interactions investigated in the context of Coronavirus

        try:
            print("\nCoronavirus...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Coronavirus.zip",
                os.path.join(self.path_tmp, "Coronavirus.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Coronavirus.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Coronavirus.zip"))

        except:

            print("\nFailed - Coronavirus downloading!")

        # Cyanobacteria - Interaction dataset based on Cyanobacteria proteins and related species

        try:
            print("\nCyanobacteria...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Cyanobacteria.zip",
                os.path.join(self.path_tmp, "Cyanobacteria.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Cyanobacteria.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Cyanobacteria.zip"))

        except:

            print("\nFailed - Cyanobacteria downloading!")

        # Diabetes - Interactions investigated in the context of Diabetes

        try:
            print("\nDiabetes...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Diabetes.zip",
                os.path.join(self.path_tmp, "Diabetes.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Diabetes.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Diabetes.zip"))

        except:

            print("\nFailed - Diabetes downloading!")

        # Huntington's - Publications describing interactions involved in Huntington's disease

        try:
            print("\nHuntington...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Huntington's.zip",
                os.path.join(self.path_tmp, "Huntington.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Huntington.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Huntington.zip"))

        except:

            print("\nFailed - Huntington downloading!")

        # IBD - Inflammatory bowel disease

        try:
            print("\nIBD...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/IBD.zip",
                os.path.join(self.path_tmp, "IBD.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "IBD.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "IBD.zip"))

        except:

            print("\nFailed - IBD downloading!")

        # Neurodegeneration - Publications depicting interactions involved in neurodegenerative disease

        try:
            print("\nNeurodegeneration...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Neurodegeneration.zip",
                os.path.join(self.path_tmp, "Neurodegeneration.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Neurodegeneration.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Neurodegeneration.zip"))

        except:

            print("\nFailed - Neurodegeneration downloading!")

        # Parkinsons - Interactions investigated in the context of Parkinsons disease

        try:
            print("\nParkinsons...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Parkinsons.zip",
                os.path.join(self.path_tmp, "Parkinsons.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Parkinsons.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Parkinsons.zip"))

        except:

            print("\nFailed - Parkinsons downloading!")

        # Rare Diseases - Interactions investigated in the context of Rare genetic diseases

        try:
            print("\nRare Diseases...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Rare_diseases.zip",
                os.path.join(self.path_tmp, "Rare_diseases.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Rare_diseases.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Rare_diseases.zip"))

        except:

            print("\nFailed - Rare Diseases downloading!")

        # Ulcerative colitis - Interactions of proteins identified as having a link to ulcerative colitis

        try:
            print("\nUlcerative colitis...")
            urllib.request.urlretrieve(
                "https://ftp.ebi.ac.uk/pub/databases/intact/current/psi30/datasets/Ulcerative_colitis.zip",
                os.path.join(self.path_tmp, "Ulcerative_colitis.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "Ulcerative_colitis.zip"), "r"
            ) as zip_ref:
                zip_ref.extractall(self.path_tmp)

            os.remove(os.path.join(self.path_tmp, "Ulcerative_colitis.zip"))

        except:

            print("\nFailed - Ulcerative colitis downloading!")

    def XML_to_dict(self):
        mutual_dcit = pd.DataFrame()
        for source in tqdm(os.listdir(self.path_tmp)):
            print("\n\n" + source)
            for int_id in tqdm(os.listdir(os.path.join(self.path_tmp, source))):
                if "negative" not in int_id:
                    with open(
                        os.path.join(self.path_tmp, source, int_id),
                        "r",
                        encoding="utf-8",
                    ) as file:
                        xml_content = file.read()

                    xml = BeautifulSoup(xml_content, "xml")

                    del xml_content

                    tmp = xml.find_all("interactor")

                    interactors = {
                        "id": [],
                        "gene_name": [],
                        "full_name": [],
                        "species": [],
                        "interactor_type": [],
                    }

                    for des in tmp:

                        interactor_type_tag = des.find("interactorType")

                        int_type = [
                            full_name_tag.get_text()
                            for full_name_tag in interactor_type_tag.find_all(
                                "fullName"
                            )
                        ]

                        ids = int(des.get("id"))
                        fullName = des.find("fullName").text
                        gene_name = des.find("alias", attrs={"type": "gene name"})
                        if gene_name:
                            gene_name = gene_name.text.strip()
                        else:
                            gene_name = des.find("primaryRef")
                            if gene_name:
                                gene_n = re.sub('.*id="', "", str(gene_name))
                                gene_n = re.sub('".*', "", str(gene_n))
                                gene_name = "Non-gene product [" + gene_n + "]"

                        tmp2 = des.find_all("organism")
                        species = []
                        for des2 in tmp2:
                            species.append(des2.find("fullName").text)

                        # Append the data to the list
                        interactors["id"].append(ids)
                        interactors["gene_name"].append(gene_name)
                        interactors["full_name"].append(fullName)
                        interactors["species"].append(species[0])
                        interactors["interactor_type"].append(int_type[0])

                    del tmp
                    del tmp2
                    tmp = xml.find_all("interaction")

                    interactions = {
                        "gene_interaction": [],
                        "gene_1_id": [],
                        "gene_2_id": [],
                        "experiment_id": [],
                        "interaction_type": [],
                        "gene_1_biological_role": [],
                        "gene_2_biological_role": [],
                        "gene_1_experimental_role": [],
                        "gene_2_experimental_role": [],
                    }

                    for n, des in enumerate(tmp):
                        interaction_name = des.find("shortLabel").text

                        interactor_refs = des.find_all("interactorRef")
                        interactor_refs = [int(ref.text) for ref in interactor_refs]

                        biological_roles = des.find_all("biologicalRole")
                        biological_roles = [
                            role.find("fullName").text for role in biological_roles
                        ]

                        experimentalRole = des.find_all("experimentalRole")
                        experimentalRole = [
                            role.find("fullName").text for role in experimentalRole
                        ]

                        interactionType = des.find_all("interactionType")
                        interactionType = [
                            role.find("fullName").text for role in interactionType
                        ]

                        experimentList = des.find_all("experimentList")
                        experimentList = [
                            int(role.find("experimentRef").text)
                            for role in experimentList
                        ]

                        if len(interactor_refs) == 2:
                            interactions["gene_interaction"].append(interaction_name)
                            interactions["gene_1_id"].append(interactor_refs[0])
                            interactions["gene_2_id"].append(interactor_refs[1])
                            interactions["experiment_id"].append(experimentList[0])
                            interactions["interaction_type"].append(interactionType[0])
                            interactions["gene_1_biological_role"].append(
                                biological_roles[0]
                            )
                            interactions["gene_2_biological_role"].append(
                                biological_roles[1]
                            )
                            interactions["gene_1_experimental_role"].append(
                                experimentalRole[0]
                            )
                            interactions["gene_2_experimental_role"].append(
                                experimentalRole[1]
                            )
                        elif (
                            len(interactor_refs) == 1
                            and biological_roles[0] == "putative self"
                        ):
                            interactions["gene_interaction"].append(interaction_name)
                            interactions["gene_1_id"].append(interactor_refs[0])
                            interactions["gene_2_id"].append(interactor_refs[0])
                            interactions["experiment_id"].append(experimentList[0])
                            interactions["interaction_type"].append(interactionType[0])
                            interactions["gene_1_biological_role"].append(
                                biological_roles[0]
                            )
                            interactions["gene_2_biological_role"].append(
                                biological_roles[0]
                            )
                            interactions["gene_1_experimental_role"].append(
                                experimentalRole[0]
                            )
                            interactions["gene_2_experimental_role"].append(
                                experimentalRole[0]
                            )

                    # 'experimentDescription'
                    del (
                        tmp,
                        interaction_name,
                        interactor_refs,
                        biological_roles,
                        experimentalRole,
                        experimentList,
                    )

                    tmp = xml.find_all("experimentDescription")

                    del xml
                    experimental = {
                        "ExperimentID": [],
                        "PublicationTitle": [],
                        "Journal": [],
                        "PublicationYear": [],
                        "AuthorList": [],
                        "Model": [],
                        "Detection_method": [],
                    }

                    for des in tmp:
                        try:
                            experiment_id = int(des.get("id"))
                        except:
                            experiment_id = None

                        try:
                            publication_title = des.find(
                                "attribute", attrs={"name": "publication title"}
                            ).text
                        except:
                            publication_title = None

                        try:
                            journal = des.find(
                                "attribute", attrs={"name": "journal"}
                            ).text
                        except:
                            journal = None

                        try:
                            publication_year = des.find(
                                "attribute", attrs={"name": "publication year"}
                            ).text
                        except:
                            publication_year = None

                        try:
                            author_list = des.find(
                                "attribute", attrs={"name": "author-list"}
                            ).text
                        except:
                            author_list = None

                        try:
                            models = des.find_all("hostOrganismList")
                            model = []
                            for model_t in models:
                                models2 = model_t.find_all("fullName")
                                for t in models2:
                                    model.append(t.text)

                            model = ", ".join(model)

                        except:
                            models = None

                        try:
                            detection_method = des.find_all(
                                "interactionDetectionMethod"
                            )
                            detection = []
                            for dect in detection_method:
                                dect2 = dect.find_all("fullName")
                                for t in dect2:
                                    detection.append(t.text)

                            detection = ", ".join(detection)

                        except:
                            detection = None

                        # Append the data to the list

                        experimental["ExperimentID"].append(experiment_id),
                        experimental["PublicationTitle"].append(publication_title),
                        experimental["Journal"].append(journal),
                        experimental["PublicationYear"].append(publication_year),
                        experimental["AuthorList"].append(author_list),
                        experimental["Detection_method"].append(detection)
                        experimental["Model"].append(model)
                        del (
                            journal,
                            detection,
                            detection_method,
                            models,
                            model,
                            publication_year,
                            author_list,
                            experiment_id,
                            publication_title,
                        )

                    del tmp

                    experimental = pd.DataFrame(experimental)
                    interactions = pd.DataFrame(interactions)
                    interactors = pd.DataFrame(interactors)
                    interactors_g1 = interactors.copy()
                    interactors_g1.columns = interactors_g1.columns + "_1"
                    interactors_g2 = interactors.copy()
                    interactors_g2.columns = interactors_g2.columns + "_2"

                    del interactors

                    interactions = pd.merge(
                        interactions,
                        experimental,
                        left_on="experiment_id",
                        right_on="ExperimentID",
                        how="left",
                    )
                    interactions = pd.merge(
                        interactions,
                        interactors_g1,
                        left_on="gene_1_id",
                        right_on="id_1",
                        how="left",
                    )
                    try:
                        interactions = pd.merge(
                            interactions,
                            interactors_g2,
                            left_on="gene_2_id",
                            right_on="id_2",
                            how="left",
                        )
                        interactions = interactions.drop(
                            [
                                "gene_1_id",
                                "gene_2_id",
                                "experiment_id",
                                "ExperimentID",
                                "id_1",
                                "id_2",
                            ],
                            axis=1,
                        )

                    except:
                        interactions = interactions.drop(
                            [
                                "gene_1_id",
                                "gene_2_id",
                                "experiment_id",
                                "ExperimentID",
                                "id_1",
                            ],
                            axis=1,
                        )

                    interactions["source"] = str(source)
                    interactions["set_id"] = str(int_id)

                    mutual_dcit = pd.concat([mutual_dcit, pd.DataFrame(interactions)])

        mutual_dcit = mutual_dcit.reset_index(drop=True)

        print("Dividing the data...")
        mutual_dcit_non_gene = pd.DataFrame()

        rm_list = []

        for i, e in enumerate(tqdm(mutual_dcit["gene_interaction"])):
            if (
                "Non-gene product".upper() in mutual_dcit["gene_name_1"][i].upper()
                or "Non-gene product".upper() in mutual_dcit["gene_name_2"][i].upper()
            ):
                rm_list.append(i)

        mutual_dcit_non_gene = mutual_dcit.loc[rm_list, :]
        mutual_dcit = mutual_dcit.drop(rm_list)

        mutual_dcit = mutual_dcit.reset_index(drop=True)

        mutual_dcit_non_gene = mutual_dcit_non_gene.reset_index(drop=True)

        mutual_dcit_non_gene = mutual_dcit_non_gene.to_dict(orient="list")

        mutual_dcit = mutual_dcit.to_dict(orient="list")

        try:
            shutil.rmtree(self.path_tmp)
            os.makedirs(self.path_tmp)
            print("The temporary file was removed successfully")
        except OSError as e:
            print(f"Error deleting the file: {e}")

        return {"gene_product": mutual_dcit, "non_gene_product": mutual_dcit_non_gene}

    def download_IntAct_data(self):
        """
        This method downloads and returns IntAct data.

        Source: https://www.ebi.ac.uk/intact/home

        Returns:
            dict (dict) - IntAct data
        """

        try:

            self.download_IntAct()
            IntAct = self.XML_to_dict()

            return IntAct

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    # DISEASE_download
    def download_diseases(self):
        """
        This method downloads and returns Diseases data.

        Source: https://diseases.jensenlab.org/Search


        Returns:
            dict (dict) - diseases data
        """

        print("\n")
        print("DISEASES data downloading...")

        try:

            files_to_download = {
                "knowledge_disease.tsv": "https://download.jensenlab.org/human_disease_knowledge_filtered.tsv",
                "mining_disease.tsv": "https://download.jensenlab.org/human_disease_textmining_filtered.tsv",
                "experiments_disease.tsv": "https://download.jensenlab.org/human_disease_experiments_filtered.tsv",
            }

            for file_name, url in files_to_download.items():
                file_path = os.path.join(self.path_tmp, file_name)
                try:
                    # Create a request with headers
                    req = urllib.request.Request(
                        url, headers={"User-Agent": "Mozilla/5.0"}
                    )
                    with (
                        urllib.request.urlopen(req) as response,
                        open(file_path, "wb") as out_file,
                    ):
                        out_file.write(response.read())
                    print(f"Downloaded {file_name} successfully.")
                except urllib.error.HTTPError as e:
                    print(f"HTTP error occurred while downloading {file_name}: {e}")
                except urllib.error.URLError as e:
                    print(f"URL error occurred while downloading {file_name}: {e}")
                except Exception as e:
                    print(
                        f"An unexpected error occurred while downloading {file_name}: {e}"
                    )

            knowledge = pd.read_csv(
                os.path.join(self.path_tmp, "knowledge_disease.tsv"),
                sep="\t",
                header=None,
            )
            experiment = pd.read_csv(
                os.path.join(self.path_tmp, "experiments_disease.tsv"),
                sep="\t",
                header=None,
            )
            mining = pd.read_csv(
                os.path.join(self.path_tmp, "mining_disease.tsv"), sep="\t", header=None
            )

            disease = pd.concat([knowledge, experiment, mining])

            disease = disease[[0, 1, 3]]

            disease.columns = ["gene", "protein", "disease"]

            disease = disease.drop_duplicates()

            dictionary = disease.to_dict(orient="list")

            try:
                os.remove(os.path.join(self.path_tmp, "knowledge_disease.tsv"))
                os.remove(os.path.join(self.path_tmp, "experiments_disease.tsv"))
                os.remove(os.path.join(self.path_tmp, "mining_disease.tsv"))
                print("The temporary file was removed successfully")
            except OSError as e:
                print(f"Error deleting the file: {e}")

            return dictionary

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    # VIRUSES_download
    def download_viral_deiseases(self):
        """
        This method downloads and returns ViMIC (viruses) data.

        Source: http://bmtongji.cn/ViMIC/index.php


        Returns:
            dict (dict) - viruses (ViMIC) data
        """

        print("\n")
        print("ViMIC data downloading...")

        try:

            urllib.request.urlretrieve(
                "http://bmtongji.cn/ViMIC/downloaddata/targetgene/Target_gene.xlsx",
                os.path.join(self.path_tmp, "viruse_disease.xlsx"),
            )

            viruses = pd.read_excel(os.path.join(self.path_tmp, "viruse_disease.xlsx"))

            dictionary = viruses.to_dict(orient="list")

            try:
                os.remove(os.path.join(self.path_tmp, "viruse_disease.xlsx"))
                print("The temporary file was removed successfully")
            except OSError as e:
                print(f"Error deleting the file: {e}")

            return dictionary

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    # HPA download
    def download_HPA(self):
        """
        This method downloads and returns Human Protein Atlas (HPA) tissue/cell data.

        Source: https://www.proteinatlas.org/


        Returns:
            dict (dict) - HPA data
        """

        print("\n")
        print("HPA data downloading...")

        try:
            urllib.request.urlretrieve(
                "https://www.proteinatlas.org/download/proteinatlas.tsv.zip",
                os.path.join(self.path_tmp, "proteinatlas.tsv.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "proteinatlas.tsv.zip"), "r"
            ) as zip_ref:
                with zip_ref.open("proteinatlas.tsv", "r") as f_in:
                    with open(
                        os.path.join(self.path_tmp, "proteinatlas.tsv"), "wb"
                    ) as f_out:
                        shutil.copyfileobj(f_in, f_out)

            HPA = pd.read_csv(os.path.join(self.path_tmp, "proteinatlas.tsv"), sep="\t")

            try:
                os.remove(os.path.join(self.path_tmp, "proteinatlas.tsv.zip"))
                os.remove(os.path.join(self.path_tmp, "proteinatlas.tsv"))

                print("The temporary file was removed successfully")
            except OSError as e:
                print(f"Error deleting the file: {e}")

            dictionary = HPA.to_dict(orient="list")

            return dictionary

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    # STRING
    def download_string(self):
        """
        This method downloads and returns STRING human/mouse/rat interaction data.

        Source: https://string-db.org/


        Returns:
            dict (dict) - STRING data
        """

        print("\n")
        print("STRING data downloading...")

        try:
            urllib.request.urlretrieve(
                "https://stringdb-downloads.org/download/protein.links.full.v12.0/9606.protein.links.full.v12.0.txt.gz",
                os.path.join(self.path_tmp, "inter_human.txt.gz"),
            )
            urllib.request.urlretrieve(
                "https://stringdb-downloads.org/download/protein.info.v12.0/9606.protein.info.v12.0.txt.gz",
                os.path.join(self.path_tmp, "info_human.txt.gz"),
            )

            with gzip.open(
                os.path.join(self.path_tmp, "inter_human.txt.gz"), "r"
            ) as f_in:
                with open(
                    os.path.join(self.path_tmp, "inter_human.txt"), "wb"
                ) as f_out:
                    shutil.copyfileobj(f_in, f_out)

            with gzip.open(
                os.path.join(self.path_tmp, "info_human.txt.gz"), "r"
            ) as f_in:
                with open(os.path.join(self.path_tmp, "info_human.txt"), "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            urllib.request.urlretrieve(
                "https://stringdb-downloads.org/download/protein.links.full.v12.0/10116.protein.links.full.v12.0.txt.gz",
                os.path.join(self.path_tmp, "inter_rat.txt.gz"),
            )
            urllib.request.urlretrieve(
                "https://stringdb-downloads.org/download/protein.info.v12.0/10116.protein.info.v12.0.txt.gz",
                os.path.join(self.path_tmp, "info_rat.txt.gz"),
            )

            with gzip.open(
                os.path.join(self.path_tmp, "inter_rat.txt.gz"), "r"
            ) as f_in:
                with open(os.path.join(self.path_tmp, "inter_rat.txt"), "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            with gzip.open(os.path.join(self.path_tmp, "info_rat.txt.gz"), "r") as f_in:
                with open(os.path.join(self.path_tmp, "info_rat.txt"), "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            urllib.request.urlretrieve(
                "https://stringdb-downloads.org/download/protein.links.full.v12.0/10090.protein.links.full.v12.0.txt.gz",
                os.path.join(self.path_tmp, "inter_mouse.txt.gz"),
            )
            urllib.request.urlretrieve(
                "https://stringdb-downloads.org/download/protein.info.v12.0/10090.protein.info.v12.0.txt.gz",
                os.path.join(self.path_tmp, "info_mouse.txt.gz"),
            )

            with gzip.open(
                os.path.join(self.path_tmp, "inter_mouse.txt.gz"), "r"
            ) as f_in:
                with open(
                    os.path.join(self.path_tmp, "inter_mouse.txt"), "wb"
                ) as f_out:
                    shutil.copyfileobj(f_in, f_out)

            with gzip.open(
                os.path.join(self.path_tmp, "info_mouse.txt.gz"), "r"
            ) as f_in:
                with open(os.path.join(self.path_tmp, "info_mouse.txt"), "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            string_hh = pd.read_csv(
                os.path.join(self.path_tmp, "inter_human.txt"), sep=" "
            )

            string_ih = pd.read_csv(
                os.path.join(self.path_tmp, "info_human.txt"), sep="\t"
            )

            string_hm = pd.read_csv(
                os.path.join(self.path_tmp, "inter_mouse.txt"), sep=" "
            )

            string_im = pd.read_csv(
                os.path.join(self.path_tmp, "info_mouse.txt"), sep="\t"
            )

            string_hr = pd.read_csv(
                os.path.join(self.path_tmp, "inter_rat.txt"), sep=" "
            )

            string_ir = pd.read_csv(
                os.path.join(self.path_tmp, "info_rat.txt"), sep="\t"
            )

            dictionary = {
                "human_ppi": string_hh.to_dict(orient="list"),
                "human_annotations": string_ih.to_dict(orient="list"),
                "mouse_ppi": string_hm.to_dict(orient="list"),
                "mouse_annotations": string_im.to_dict(orient="list"),
                "rat_ppi": string_hr.to_dict(orient="list"),
                "rat_annotations": string_ir.to_dict(orient="list"),
            }

            try:
                os.remove(os.path.join(self.path_tmp, "inter_human.txt"))
                os.remove(os.path.join(self.path_tmp, "info_human.txt"))
                os.remove(os.path.join(self.path_tmp, "inter_mouse.txt"))
                os.remove(os.path.join(self.path_tmp, "info_mouse.txt"))
                os.remove(os.path.join(self.path_tmp, "inter_human.txt.gz"))
                os.remove(os.path.join(self.path_tmp, "info_human.txt.gz"))
                os.remove(os.path.join(self.path_tmp, "inter_mouse.txt.gz"))
                os.remove(os.path.join(self.path_tmp, "info_mouse.txt.gz"))
                os.remove(os.path.join(self.path_tmp, "inter_rat.txt"))
                os.remove(os.path.join(self.path_tmp, "info_rat.txt"))
                os.remove(os.path.join(self.path_tmp, "inter_rat.txt.gz"))
                os.remove(os.path.join(self.path_tmp, "info_rat.txt.gz"))

                print("The temporary file was removed successfully")
            except OSError as e:
                print(f"Error deleting the file: {e}")

            return dictionary

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def scpecies_concatenate(self, string):

        mouse = pd.DataFrame(string["mouse_annotations"])
        mouse["preferred_name"] = [x.upper() for x in mouse["preferred_name"]]
        human = pd.DataFrame(string["human_annotations"])
        human["preferred_name"] = [x.upper() for x in human["preferred_name"]]
        rat = pd.DataFrame(string["rat_annotations"])
        rat["preferred_name"] = [x.upper() for x in rat["preferred_name"]]
        human["species"] = "Homo sapiens"
        mouse["species"] = "Mus musculus"
        rat["species"] = "Rattus norvegicus"

        mouse_ppi = pd.DataFrame(string["mouse_ppi"])
        name_mapping = dict(zip(mouse["#string_protein_id"], mouse["preferred_name"]))
        mouse_ppi["protein1"] = mouse_ppi["protein1"].map(name_mapping)
        mouse_ppi["protein2"] = mouse_ppi["protein2"].map(name_mapping)
        mouse_ppi["species"] = "Mus musculus"

        human_ppi = pd.DataFrame(string["human_ppi"])
        name_mapping = dict(zip(human["#string_protein_id"], human["preferred_name"]))
        human_ppi["protein1"] = human_ppi["protein1"].map(name_mapping)
        human_ppi["protein2"] = human_ppi["protein2"].map(name_mapping)
        human_ppi["species"] = "Homo sapiens"

        rat_ppi = pd.DataFrame(string["rat_ppi"])
        name_mapping = dict(zip(rat["#string_protein_id"], rat["preferred_name"]))
        rat_ppi["protein1"] = rat_ppi["protein1"].map(name_mapping)
        rat_ppi["protein2"] = rat_ppi["protein2"].map(name_mapping)
        rat_ppi["species"] = "Rattus norvegicus"

        ppi = pd.concat([mouse_ppi, human_ppi, rat_ppi])

        del human_ppi, mouse_ppi, rat_ppi

        metadata = pd.concat([human, mouse, rat])
        metadata = (
            metadata.groupby("preferred_name")
            .agg({"species": list, "annotation": list, "protein_size": list})
            .reset_index()
        )

        ppi = ppi.to_dict(orient="list")
        metadata = metadata.to_dict(orient="list")

        dictionary = {"ppi": ppi, "metadata": metadata}

        return dictionary

    # KEGG

    #################################################################################

    def download_kegg(self):
        """
        This method downloads and returns KEGG data.

        Source: https://www.genome.jp/kegg/


        Returns:
            dict (dict) - KEGG data
        """

        print("\n")
        print("KEGG data downloading...")

        try:

            urllib.request.urlretrieve(
                "https://www.kegg.jp/kegg-bin/download_htext?htext=ko00001.keg&format=json&filedir=",
                os.path.join(self.path_tmp, "kegg.json"),
            )

            with open(os.path.join(self.path_tmp, "kegg.json")) as j:
                kegg = json.load(j)

            first = []
            second = []
            third = []
            fourth = []

            for n, inx in enumerate(tqdm(kegg["children"])):
                for i, inx in enumerate(kegg["children"][n]["children"]):
                    for j, inx in enumerate(
                        kegg["children"][n]["children"][i]["children"]
                    ):
                        try:
                            kegg["children"][n]["children"][i]["children"][j][
                                "children"
                            ]
                        except:
                            break
                        for k, inx in enumerate(
                            kegg["children"][n]["children"][i]["children"][j][
                                "children"
                            ]
                        ):
                            try:
                                kegg["children"][n]["children"][i]["children"][j][
                                    "children"
                                ][k]
                            except:
                                break

                            first.append(
                                re.sub(r"\d+", "", kegg["children"][n]["name"])[
                                    1 : len(
                                        re.sub(r"\d+", "", kegg["children"][n]["name"])
                                    )
                                ]
                            )
                            second.append(
                                re.sub(
                                    r"\d+",
                                    "",
                                    kegg["children"][n]["children"][i]["name"],
                                )[
                                    1 : len(
                                        re.sub(
                                            r"\d+",
                                            "",
                                            kegg["children"][n]["children"][i]["name"],
                                        )
                                    )
                                ]
                            )
                            third.append(
                                re.sub(
                                    r" \[.*",
                                    "",
                                    str(
                                        kegg["children"][n]["children"][i]["children"][
                                            j
                                        ]["name"]
                                    )[
                                        6 : len(
                                            str(
                                                kegg["children"][n]["children"][i][
                                                    "children"
                                                ][j]["name"]
                                            )
                                        )
                                    ],
                                )
                            )
                            fourth.append(
                                str(
                                    kegg["children"][n]["children"][i]["children"][j][
                                        "children"
                                    ][k]["name"]
                                )[
                                    8 : len(
                                        str(
                                            kegg["children"][n]["children"][i][
                                                "children"
                                            ][j]["children"][k]["name"]
                                        )
                                    )
                                ]
                            )

            df = pd.DataFrame(
                {"1st": first, "2nd": second, "3rd": third, "4th": fourth}
            ).reset_index(drop=True)
            df = df.drop_duplicates().reset_index(drop=True)
            df["gene"] = [re.sub(";.*", "", y).split(",") for y in df["4th"]]
            df["name"] = [
                re.sub(re.sub(";.*", "", y) + "; ", "", df["4th"][n])
                for n, y in enumerate(df["4th"])
            ]
            df = df.drop(["4th"], axis=1)
            df = df.reset_index(drop=True)

            df = df.to_dict(orient="list")

            try:
                os.remove(os.path.join(self.path_tmp, "kegg.json"))

                print("The temporary file was removed successfully")
            except OSError as e:
                print(f"Error deleting the file: {e}")

            return df

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    # REACTOME

    def download_reactome(self):
        """
        This method downloads and returns REACTOME data.

        Source: https://reactome.org/


        Returns:
            dict (dict) - REACTOME data
        """

        print("\n")
        print("REACTOME data downloading...")

        try:

            urllib.request.urlretrieve(
                "https://reactome.org/download/current/ReactomePathways.gmt.zip",
                os.path.join(self.path_tmp, "reactome.zip"),
            )

            with zipfile.ZipFile(
                os.path.join(self.path_tmp, "reactome.zip"), "r"
            ) as zip_ref:
                # Extract all the files to the destination directory
                zip_ref.extractall(os.path.join(self.path_tmp, "reactome"))

            with open(
                os.path.join(self.path_tmp, "reactome", "ReactomePathways.gmt"), "r"
            ) as file:
                # Iterate through the lines of the file
                path_name = []
                path_id = []
                gen = []
                for line in file:
                    tmp = line.strip().split("\t")
                    for li in range(2, len(tmp)):
                        path_name.append(tmp[0])
                        path_id.append(tmp[1])
                        gen.append(tmp[li])

            df = pd.DataFrame({"path_name": path_name, "path_id": path_id, "gene": gen})

            connections = pd.read_csv(
                "https://reactome.org/download/current/Complex_2_Pathway_human.txt",
                header=0,
                sep="\t",
            )

            connections = connections.to_dict(orient="list")

            low_level_paths = pd.read_csv(
                "https://reactome.org/download/current/ComplexParticipantsPubMedIdentifiers_human.txt",
                header=0,
                sep="\t",
            )

            low_level_paths = low_level_paths.to_dict(orient="list")

            df = df.reset_index(drop=True)

            df = df.to_dict(orient="list")

            dictionary = {
                "gene_info": df,
                "connections": connections,
                "paths": low_level_paths,
            }

            try:
                os.remove(
                    os.path.join(self.path_tmp, "reactome", "ReactomePathways.gmt")
                )
                os.remove(os.path.join(self.path_tmp, "reactome.zip"))
                shutil.rmtree(os.path.join(self.path_tmp, "reactome"))

                print("The temporary file was removed successfully")
            except OSError as e:
                print(f"Error deleting the file: {e}")

            return dictionary

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def download_go_connections(self):

        response = requests.get("http://purl.obolibrary.org/obo/go.obo")

        GO_id = []
        name = []
        name_space = []
        synonym = []
        definition = []
        children = []
        obsolete = []
        alternative_id = []
        list_of_lines = []
        intersection = []
        relationship = []
        part_of = []

        l = 0
        if response.status_code == 200:

            # Iterate through each line in the response content

            term = []
            for n, line in enumerate(response.iter_lines()):
                line = line.decode("utf-8")
                list_of_lines.append(line)

                if "[Term]" in str(line):
                    term.append(n)

            for en, j in enumerate(range(len(term))):
                tmp_child = []
                tmp_syn = []
                tmp_alt = []
                tmp_int = []
                tmp_relationship = []
                tmp_part_of = []

                if j <= len(term) - 2:
                    tmp = list_of_lines[term[j] : term[j + 1]]
                    for l in tmp:
                        if "id: GO" in l and "_id:" not in l:
                            GO_id.append(re.sub("id: ", "", l))
                        if "name:" in l:
                            name.append(re.sub("name: ", "", l))
                        if "is_obsolete:" in l:
                            obsolete.append(bool(re.sub("is_obsolete: ", "", l)))
                        if "namespace:" in l:
                            name_space.append(re.sub("namespace: ", "", l))
                        if "def:" in l:
                            definition.append(
                                re.sub(
                                    r"\[.*", "", re.sub('"', "", re.sub("def: ", "", l))
                                )
                            )
                        if "synonym:" in l:
                            tmp_syn.append(
                                re.sub(
                                    r"\[.*",
                                    "",
                                    re.sub('"', "", re.sub("synonym: ", "", l)),
                                )
                            )
                        if "is_a:" in l:
                            tmp_child.append(
                                re.sub(
                                    r"\[.*",
                                    "",
                                    re.sub('"', "", re.sub("is_a: ", "", l)),
                                )
                            )
                        if "alt_id:" in l:
                            tmp_alt.append(
                                re.sub(
                                    r"\[.*",
                                    "",
                                    re.sub('"', "", re.sub("alt_id: ", "", l)),
                                )
                            )
                        if "intersection_of:" in l:
                            tmp_int.append(
                                re.sub('"', "", re.sub("intersection_of: ", "", l))
                            )
                        if "relationship:" in l:
                            tmp_relationship.append(
                                re.sub(
                                    "",
                                    "",
                                    re.sub('"', "", re.sub("relationship: ", "", l)),
                                )
                            )
                        if "part_of:" in l:
                            tmp_part_of.append(
                                re.sub(
                                    "", "", re.sub('"', "", re.sub("part_of: ", "", l))
                                )
                            )

                    if len(tmp_syn) == 0:
                        synonym.append(None)
                    else:
                        synonym.append(tmp_syn)
                    if len(tmp_alt) == 0:
                        alternative_id.append(None)
                    else:
                        alternative_id.append(tmp_alt)
                    if len(tmp_int) == 0:
                        intersection.append(None)
                    else:
                        intersection.append(tmp_int)
                    if len(tmp_relationship) == 0:
                        relationship.append(None)
                    else:
                        relationship.append(tmp_relationship)
                    if len(tmp_part_of) == 0:
                        part_of.append(None)
                    else:
                        part_of.append(tmp_part_of)
                    if len(tmp_child) == 0:
                        children.append(None)
                    else:
                        children.append(tmp_child)

                    if len(GO_id) < en + 1:
                        GO_id.append(None)
                    if len(name) < en + 1:
                        name.append(None)
                    if len(obsolete) < en + 1:
                        obsolete.append(False)
                    if len(name_space) < en + 1:
                        name_space.append(None)
                    if len(definition) < en + 1:
                        definition.append(None)

        df = {
            "GO_id": GO_id,
            "name": name,
            "name_space": name_space,
            "synonym": synonym,
            "definition": definition,
            "definition": definition,
            "alternative_id": alternative_id,
            "children": children,
            "intersection": intersection,
            "relationship": relationship,
            "part_of": part_of,
            "obsolete": obsolete,
        }

        df = pd.DataFrame(df)

        df["is_a_ids"] = None
        df["part_of_ids"] = None
        df["has_part_ids"] = None
        df["regulates_ids"] = None
        df["negatively_regulates_ids"] = None
        df["positively_regulates_ids"] = None
        df["is_a_des"] = None
        df["part_of_des"] = None
        df["regulates_des"] = None
        df["negatively_regulates_des"] = None
        df["positively_regulates_des"] = None
        df["has_part_des"] = None

        ####
        for n, inter in enumerate(tqdm(df["intersection"])):
            if inter != None:
                if (
                    "regulates" in df["intersection"][n][1]
                    and "negatively_regulates" not in df["intersection"][n][1]
                    and "positively_regulates" not in df["intersection"][n][1]
                ):
                    #
                    if df["regulates_ids"][n] == None:
                        df["regulates_ids"][n] = [
                            re.sub(" !.*", "", df["intersection"][n][0])
                        ]
                    else:
                        df["regulates_ids"][n] = df["regulates_ids"][n] + [
                            re.sub(" !.*", "", df["intersection"][n][0])
                        ]

                    if df["regulates_des"][n] == None:
                        df["regulates_des"][n] = [
                            re.sub(".*! ", "", df["intersection"][n][0])
                        ]
                    else:
                        df["regulates_des"][n] = df["regulates_des"][n] + [
                            re.sub(".*! ", "", df["intersection"][n][0])
                        ]

                    #
                    if df["regulates_ids"][n] == None:
                        df["regulates_ids"][n] = [
                            re.sub(
                                "regulates ",
                                "",
                                re.sub(" !.*", "", df["intersection"][n][1]),
                            )
                        ]
                    else:
                        df["regulates_ids"][n] = df["regulates_ids"][n] + [
                            re.sub(
                                "regulates ",
                                "",
                                re.sub(" !.*", "", df["intersection"][n][1]),
                            )
                        ]

                    if df["regulates_des"][n] == None:
                        df["regulates_des"][n] = [
                            re.sub(".*! ", "", df["intersection"][n][1])
                        ]
                    else:
                        df["regulates_des"][n] = df["regulates_des"][n] + [
                            re.sub(".*! ", "", df["intersection"][n][1])
                        ]

                elif (
                    "positively_regulates" in df["intersection"][n][1]
                    and "negatively_regulates" not in df["intersection"][n][1]
                ):
                    #
                    if df["positively_regulates_ids"][n] == None:
                        df["positively_regulates_ids"][n] = [
                            re.sub(" !.*", "", df["intersection"][n][0])
                        ]
                    else:
                        df["positively_regulates_ids"][n] = df[
                            "positively_regulates_ids"
                        ][n] + [re.sub(" !.*", "", df["intersection"][n][0])]

                    if df["positively_regulates_des"][n] == None:
                        df["positively_regulates_des"][n] = [
                            re.sub(".*! ", "", df["intersection"][n][0])
                        ]
                    else:
                        df["positively_regulates_des"][n] = df[
                            "positively_regulates_des"
                        ][n] + [re.sub(".*! ", "", df["intersection"][n][0])]

                    #
                    if df["positively_regulates_ids"][n] == None:
                        df["positively_regulates_ids"][n] = [
                            re.sub(
                                "positively_regulates ",
                                "",
                                re.sub(" !.*", "", df["intersection"][n][1]),
                            )
                        ]
                    else:
                        df["positively_regulates_ids"][n] = df[
                            "positively_regulates_ids"
                        ][n] + [
                            re.sub(
                                "positively_regulates ",
                                "",
                                re.sub(" !.*", "", df["intersection"][n][1]),
                            )
                        ]

                    if df["positively_regulates_des"][n] == None:
                        df["positively_regulates_des"][n] = [
                            re.sub(".*! ", "", df["intersection"][n][1])
                        ]
                    else:
                        df["positively_regulates_des"][n] = df[
                            "positively_regulates_des"
                        ][n] + [re.sub(".*! ", "", df["intersection"][n][1])]

                elif (
                    "negatively_regulates" in df["intersection"][n][1]
                    and "positively_regulates" not in df["intersection"][n][1]
                ):
                    #
                    if df["negatively_regulates_ids"][n] == None:
                        df["negatively_regulates_ids"][n] = [
                            re.sub(" !.*", "", df["intersection"][n][0])
                        ]
                    else:
                        df["negatively_regulates_ids"][n] = df[
                            "negatively_regulates_ids"
                        ][n] + [re.sub(" !.*", "", df["intersection"][n][0])]

                    if df["negatively_regulates_des"][n] == None:
                        df["negatively_regulates_des"][n] = [
                            re.sub(".*! ", "", df["intersection"][n][0])
                        ]
                    else:
                        df["negatively_regulates_des"][n] = df[
                            "negatively_regulates_des"
                        ][n] + [re.sub(".*! ", "", df["intersection"][n][0])]

                    #
                    if df["negatively_regulates_ids"][n] == None:
                        df["negatively_regulates_ids"][n] = [
                            re.sub(
                                "negatively_regulates ",
                                "",
                                re.sub(" !.*", "", df["intersection"][n][1]),
                            )
                        ]
                    else:
                        df["negatively_regulates_ids"][n] = df[
                            "negatively_regulates_ids"
                        ][n] + [
                            re.sub(
                                "negatively_regulates ",
                                "",
                                re.sub(" !.*", "", df["intersection"][n][1]),
                            )
                        ]

                    if df["negatively_regulates_des"][n] == None:
                        df["negatively_regulates_des"][n] = [
                            re.sub(".*! ", "", df["intersection"][n][1])
                        ]
                    else:
                        df["negatively_regulates_des"][n] = df[
                            "negatively_regulates_des"
                        ][n] + [re.sub(".*! ", "", df["intersection"][n][1])]

            if df["relationship"][n] != None:
                for f in df["relationship"][n]:
                    if (
                        "regulates" in f
                        and "negatively_regulates" not in f
                        and "positively_regulates" not in f
                    ):
                        #
                        if df["regulates_ids"][n] == None:
                            df["regulates_ids"][n] = [
                                re.sub("regulates ", "", re.sub(" !.*", "", f))
                            ]
                        else:
                            df["regulates_ids"][n] = df["regulates_ids"][n] + [
                                re.sub("regulates ", "", re.sub(" !.*", "", f))
                            ]

                        if df["regulates_des"][n] == None:
                            df["regulates_des"][n] = [re.sub(".*! ", "", f)]
                        else:
                            df["regulates_des"][n] = df["regulates_des"][n] + [
                                re.sub(".*! ", "", f)
                            ]

                    elif (
                        "positively_regulates" in f and "negatively_regulates" not in f
                    ):
                        #
                        if df["positively_regulates_ids"][n] == None:
                            df["positively_regulates_ids"][n] = [
                                re.sub(
                                    "positively_regulates ", "", re.sub(" !.*", "", f)
                                )
                            ]
                        else:
                            df["positively_regulates_ids"][n] = df[
                                "positively_regulates_ids"
                            ][n] + [
                                re.sub(
                                    "positively_regulates ", "", re.sub(" !.*", "", f)
                                )
                            ]

                        if df["positively_regulates_des"][n] == None:
                            df["positively_regulates_des"][n] = [re.sub(".*! ", "", f)]
                        else:
                            df["positively_regulates_des"][n] = df[
                                "positively_regulates_des"
                            ][n] + [re.sub(".*! ", "", f)]

                    elif (
                        "negatively_regulates" in f and "positively_regulates" not in f
                    ):
                        #
                        if df["negatively_regulates_ids"][n] == None:
                            df["negatively_regulates_ids"][n] = [
                                re.sub(
                                    "negatively_regulates ", "", re.sub(" !.*", "", f)
                                )
                            ]
                        else:
                            df["negatively_regulates_ids"][n] = df[
                                "negatively_regulates_ids"
                            ][n] + [
                                re.sub(
                                    "negatively_regulates ", "", re.sub(" !.*", "", f)
                                )
                            ]

                        if df["negatively_regulates_des"][n] == None:
                            df["negatively_regulates_des"][n] = [re.sub(".*! ", "", f)]
                        else:
                            df["negatively_regulates_des"][n] = df[
                                "negatively_regulates_des"
                            ][n] + [re.sub(".*! ", "", f)]

                    elif "has_part" in f:
                        #
                        if df["has_part_ids"][n] == None:
                            df["has_part_ids"][n] = [
                                re.sub("has_part ", "", re.sub(" !.*", "", f))
                            ]
                        else:
                            df["has_part_ids"][n] = df["has_part_ids"][n] + [
                                re.sub("has_part ", "", re.sub(" !.*", "", f))
                            ]

                        if df["has_part_des"][n] == None:
                            df["has_part_des"][n] = [re.sub(".*! ", "", f)]
                        else:
                            df["has_part_des"][n] = df["has_part_des"][n] + [
                                re.sub(".*! ", "", f)
                            ]

                    elif "part_of" in f:
                        #
                        if df["part_of_ids"][n] == None:
                            df["part_of_ids"][n] = [
                                re.sub("part_of ", "", re.sub(" !.*", "", f))
                            ]
                        else:
                            df["part_of_ids"][n] = df["part_of_ids"][n] + [
                                re.sub("part_of ", "", re.sub(" !.*", "", f))
                            ]

                        if df["part_of_des"][n] == None:
                            df["part_of_des"][n] = [re.sub(".*! ", "", f)]
                        else:
                            df["part_of_des"][n] = df["part_of_des"][n] + [
                                re.sub(".*! ", "", f)
                            ]

            if df["children"][n] != None:
                for f in df["children"][n]:
                    #
                    if df["is_a_ids"][n] == None:
                        df["is_a_ids"][n] = [re.sub(" !.*", "", f)]
                    else:
                        df["is_a_ids"][n] = df["is_a_ids"][n] + [re.sub(" !.*", "", f)]

                    if df["is_a_des"][n] == None:
                        df["is_a_des"][n] = [re.sub(".*! ", "", f)]
                    else:
                        df["is_a_des"][n] = df["is_a_des"][n] + [re.sub(".*! ", "", f)]

        df = df.drop(["children", "relationship", "intersection"], axis=1)
        df = df.to_dict(orient="list")

        return df

    def download_go_annotations(self):

        #### GO annotation mouse & human
        urllib.request.urlretrieve(
            "http://geneontology.org/gene-associations/goa_human.gaf.gz",
            os.path.join(self.path_tmp, "goa_human.gaf.gz"),
        )

        with gzip.open(os.path.join(self.path_tmp, "goa_human.gaf.gz"), "r") as f_in:
            with open(os.path.join(self.path_tmp, "goa_human.gaf"), "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        count = 0

        with open(os.path.join(self.path_tmp, "goa_human.gaf"), "r") as file:
            for line in file:
                if line.startswith("!"):
                    count += 1
                else:
                    break

        df2 = pd.read_csv(
            os.path.join(self.path_tmp, "goa_human.gaf"),
            sep="\t",
            skiprows=count,
            header=None,
        )
        df2 = df2[[0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12]]
        df2.columns = [
            "source",
            "source_id",
            "gene_name",
            "connection",
            "GO_id",
            "ref",
            "confidence_code",
            "description",
            "protein_name",
            "function",
            "tax_id",
        ]
        df2["species"] = "Homo sapiens"

        ####
        urllib.request.urlretrieve(
            "http://current.geneontology.org/annotations/mgi.gaf.gz",
            os.path.join(self.path_tmp, "mgi.gaf.gz"),
        )

        with gzip.open(os.path.join(self.path_tmp, "mgi.gaf.gz"), "r") as f_in:
            with open(os.path.join(self.path_tmp, "mgi.gaf"), "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        count = 0

        with open(os.path.join(self.path_tmp, "mgi.gaf"), "r") as file:
            for line in file:
                if line.startswith("!"):
                    count += 1
                else:
                    break

        df3 = pd.read_csv(
            os.path.join(self.path_tmp, "mgi.gaf"),
            sep="\t",
            skiprows=count,
            header=None,
        )
        df3 = df3[[0, 1, 2, 3, 4, 5, 6, 9, 10, 11, 12]]
        df3.columns = [
            "source",
            "source_id",
            "gene_name",
            "connection",
            "GO_id",
            "ref",
            "confidence_code",
            "description",
            "protein_name",
            "function",
            "tax_id",
        ]
        df3["species"] = "Mus musculus"

        annotation = pd.concat([df2, df3])

        annotation = annotation[(annotation["gene_name"] == annotation["gene_name"])]

        annotation = annotation.to_dict(orient="list")

        try:
            os.remove(os.path.join(self.path_tmp, "mgi.gaf.gz"))
            os.remove(os.path.join(self.path_tmp, "mgi.gaf"))
            os.remove(os.path.join(self.path_tmp, "goa_human.gaf.gz"))
            os.remove(os.path.join(self.path_tmp, "goa_human.gaf"))

            print("The temporary file was removed successfully")
        except OSError as e:
            print(f"Error deleting the file: {e}")

        return annotation

    def download_cell_talk(self):
        """
        This method downloads and returns CellTalk data.

        Source: https://tcm.zju.edu.cn/celltalkdb/


        Returns:
            dict (dict) - CellTalk data
        """

        print("\n")
        print("CellTalk data downloading...")

        try:

            urllib.request.urlretrieve(
                "https://drive.google.com/uc?id=1X_fyqeH1-EAAM60Bgiifp9pwr41i43Yn",
                os.path.join(self.path_tmp, "human_lr.txt"),
            )
            urllib.request.urlretrieve(
                "https://drive.google.com/uc?id=11SiiCPxiGpbkqksFn-0I4wF6Y-kJKfv8",
                os.path.join(self.path_tmp, "mouse_lr.txt"),
            )

            human = pd.read_csv(os.path.join(self.path_tmp, "human_lr.txt"), sep="\t")
            human["species"] = "Homo sapiens"

            mouse = pd.read_csv(os.path.join(self.path_tmp, "mouse_lr.txt"), sep="\t")
            mouse["species"] = "Mus musculus"

            mutual = pd.concat([human, mouse])

            del mouse, human

            os.remove(os.path.join(self.path_tmp, "human_lr.txt"))
            os.remove(os.path.join(self.path_tmp, "mouse_lr.txt"))

            return mutual.to_dict(orient="list")

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def download_cell_phone(self):
        """
        This method downloads and returns CellPhone data.

        Source: https://www.cellphonedb.org/


        Returns:
            dict (dict) - CellPhone data
        """

        print("\n")
        print("CellPhone data downloading...")

        try:

            urllib.request.urlretrieve(
                "https://drive.google.com/uc?id=17XUxYCgLcdfS3tZB4xV21ZdtqDlCJAi_",
                os.path.join(self.path_tmp, "lr.csv"),
            )

            lr = pd.read_csv(os.path.join(self.path_tmp, "lr.csv"), sep=",")

            os.remove(os.path.join(self.path_tmp, "lr.csv"))

            return lr.to_dict(orient="list")

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def download_go_term(self):
        """
        This method downloads and returns GO-TERM data.

        Source: https://geneontology.org/


        Returns:
            dict (dict) - GO-TERM data
        """

        print("\n")
        print("GO-TERM data downloading...")

        try:

            go_annotation = self.download_go_annotations()
            go_term = self.download_go_connections()

            dictionary = {"metadata": go_annotation, "connections": go_term}

            return dictionary

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def update_downloading(self, password=None):

        print("\n")
        print("Data downloading starting...")
        print(
            "Data are downloaded from many sources so this process can last several minutes..."
        )

        ref = self.download_ref()

        with open(
            os.path.join(self.path_inside, "gene_dictionary_jbio.json"), "w"
        ) as json_file:
            json.dump(ref, json_file)

        del ref

        rs_seq = self.download_rns_seq()

        for r in rs_seq.keys():

            if len(rs_seq[r]) > 0:
                print(r)

                with open(
                    os.path.join(self.path_in_inside, str(r) + ".json"), "w"
                ) as json_file:
                    json.dump(rs_seq[r], json_file)

        del rs_seq

        IntAct = self.download_IntAct_data()

        with open(os.path.join(self.path_inside, "IntAct_jbio.json"), "w") as json_file:
            json.dump(IntAct, json_file)

        del IntAct

        diseases = self.download_diseases()

        with open(
            os.path.join(self.path_inside, "diseases_jbio.json"), "w"
        ) as json_file:
            json.dump(diseases, json_file)

        del diseases

        viral_diseases = self.download_viral_deiseases()

        with open(
            os.path.join(self.path_inside, "viral_diseases_jbio.json"), "w"
        ) as json_file:
            json.dump(viral_diseases, json_file)

        del viral_diseases

        HPA = self.download_HPA()

        with open(os.path.join(self.path_inside, "HPA_jbio.json"), "w") as json_file:
            json.dump(HPA, json_file)

        del HPA

        string = self.download_string()

        string_dict = self.scpecies_concatenate(string)

        with open(os.path.join(self.path_inside, "string_jbio.json"), "w") as json_file:
            json.dump(string_dict, json_file)

        del string, string_dict

        kegg = self.download_kegg()

        with open(os.path.join(self.path_inside, "kegg_jbio.json"), "w") as json_file:
            json.dump(kegg, json_file)

        del kegg

        reactome = self.download_reactome()

        with open(
            os.path.join(self.path_inside, "reactome_jbio.json"), "w"
        ) as json_file:
            json.dump(reactome, json_file)

        del reactome

        go_term = self.download_go_term()

        with open(os.path.join(self.path_inside, "goterm_jbio.json"), "w") as json_file:
            json.dump(go_term, json_file)

        del go_term

        cell_talk = self.download_cell_talk()

        with open(
            os.path.join(self.path_inside, "cell_talk_jbio.json"), "w"
        ) as json_file:
            json.dump(cell_talk, json_file)

        del cell_talk

        cell_phone = self.download_cell_phone()

        with open(
            os.path.join(self.path_inside, "cell_phone_jbio.json"), "w"
        ) as json_file:
            json.dump(cell_phone, json_file)

        del cell_phone

        current_date = datetime.today().date()
        current_date = current_date.strftime("%d-%m-%Y")

        text = "The last GEDS update was done on " + str(current_date)

        if password != None and password.upper() == "JBS":
            text = text + "\nThe GEDS data version authorized by JBS"
            text = (
                text + "\nThe GEDS data version: GEDS-" + re.sub("-", "/", current_date)
            )
        else:
            text = text + "\nThe GEDS data version unauthorized"
            text = (
                text
                + "\nThe GEDS data version: User_custom-"
                + re.sub("-", "/", current_date)
            )

        # Open the file in write mode and save the string to it
        with open(os.path.join(self.path_inside, "update.dat"), "w") as file:
            file.write(text)

        print("\n")
        print("Data download has finished...")

    def check_last_update(self):
        """
        This method checks the last update of GEDS data used in this library

        Returns:
           date: Date of last update

        """

        with open(os.path.join(self.path_inside, "update.dat"), "r") as file:
            print("\n")
            print(file.read())


class DataAdjustment(GetData, PathMetadata):

    def __init__(self):
        super().__init__()
        self.gene_dict = None

    # Database mapping to gene dictionary functions

    def find_fetures_id(self, genome_dict, fetures_list):
        if isinstance(genome_dict, dict):
            genome_dict = pd.DataFrame(genome_dict)

        gene = []
        not_found = []
        ids = []
        for fet in tqdm(fetures_list):
            idg = genome_dict.index[
                genome_dict["possible_names"].apply(lambda x: fet.upper() in x)
            ]
            if len(idg) > 0:
                ids.append(idg)
                gene.append(fet)
            else:
                not_found.append(fet)

        return {"found_genes": gene, "found_ids": ids, "not_found": not_found}

    def find_fetures_list_id(self, genome_dict, fetures_list):
        if isinstance(genome_dict, dict):
            genome_dict = pd.DataFrame(genome_dict)

        gene = []
        not_found = []
        ids = []
        for fet_list in tqdm(fetures_list):
            idg = genome_dict.index[
                genome_dict["possible_names"].apply(
                    lambda x: any(element.upper() in fet_list for element in x)
                )
            ]
            if len(idg) > 0:
                ids.append(idg)
                gene.append(fet_list)
            else:
                not_found.append(fet_list)

        return {"found_genes": gene, "found_ids": ids, "not_found": not_found}

    def reactome_to_gene_dict(self, reactome_jbio):

        reactome = pd.DataFrame(reactome_jbio["gene_info"])

        jdci = pd.DataFrame(
            {
                "names": list(set(reactome["gene"])),
                "id": range(len(list(set(reactome["gene"])))),
            }
        )

        jdci["id"] = [int(x) for x in jdci["id"]]

        reactome = pd.merge(
            reactome,
            jdci[["names", "id"]],
            left_on="gene",
            right_on="names",
            how="left",
        )

        reactome = reactome.drop("names", axis=1)

        gene_dictionary = pd.DataFrame(self.gene_dict).reset_index(drop=True)

        reactome["gene"] = [x.upper() for x in reactome["gene"]]

        fetures_id = self.find_fetures_id(gene_dictionary, list(set(reactome["gene"])))

        gene_dictionary["id_reactome"] = None
        gene_dictionary["primary_reactome_gene"] = None

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        for inx, gene in enumerate(tqdm(fetures_id["found_genes"])):
            idr = list(
                set(reactome["id"][reactome["gene"] == fetures_id["found_genes"][inx]])
            )[0]
            gene_dictionary["id_reactome"][fetures_id["found_ids"][inx][0]] = idr
            gene_dictionary["primary_reactome_gene"][
                fetures_id["found_ids"][inx][0]
            ] = gene

        gene_dictionary = pd.DataFrame(gene_dictionary)

        for gene in tqdm(set(fetures_id["not_found"])):

            idr = list(set(reactome["id"][reactome["gene"] == gene]))[0]
            new_row = {col: [None] for col in gene_dictionary.columns}
            new_row["id_reactome"] = [idr]
            new_row["possible_names"] = [[gene]]
            new_row["species"] = [["Homo sapiens"]]
            new_row["primary_reactome_gene"] = [gene]

            gene_dictionary = pd.concat([gene_dictionary, pd.DataFrame(new_row)])

        gene_dictionary = gene_dictionary.reset_index(drop=True)

        gene_dictionary = gene_dictionary.to_dict(orient="list")
        reactome = reactome.to_dict(orient="list")
        reactome_jbio["gene_info"] = reactome

        self.gene_dict = gene_dictionary

        return reactome_jbio

    def reactome_adjustment(self, reactome_jbio):

        reactome = pd.DataFrame(reactome_jbio["gene_info"])
        connections = pd.DataFrame(reactome_jbio["connections"])
        top_level = pd.DataFrame(reactome_jbio["paths"])
        top_level["participatingComplex"] = [
            x.split("|") for x in top_level["participatingComplex"]
        ]
        top_level = top_level.explode("participatingComplex")

        tmp = reactome[["path_id", "id"]].drop_duplicates()
        tmp = tmp.groupby("path_id")[["id"]].agg(list).reset_index()

        name_mapping = dict(zip(list(tmp["path_id"]), list(tmp["id"])))
        connections["id"] = connections["pathway"].map(name_mapping)
        connections = connections.explode("id")

        connections = connections.drop_duplicates()

        tmp = reactome[["path_id", "path_name"]].drop_duplicates()
        tmp = tmp.groupby("path_id")[["path_name"]].agg(list).reset_index()

        name_mapping = dict(zip(list(tmp["path_id"]), list(tmp["path_name"])))

        connections["pathway"] = connections["pathway"].map(name_mapping)
        connections = connections.explode("pathway")

        connections["top_level_pathway"] = connections["top_level_pathway"].map(
            name_mapping
        )
        connections = connections.explode("top_level_pathway")

        tmp1 = top_level[["identifier", "name"]].drop_duplicates()
        tmp1.columns = ["0", "1"]

        tmp2 = top_level[["participatingComplex", "name"]].drop_duplicates()
        tmp2.columns = ["0", "1"]

        tmp = pd.concat([tmp1, tmp2], axis=0).drop_duplicates()

        tmp = tmp.groupby("0")[["1"]].agg(list).reset_index()

        name_mapping = dict(zip(list(tmp["0"]), list(tmp["1"])))

        connections["complex"] = connections["complex"].map(name_mapping)
        connections = connections.explode("complex")

        connections = connections.drop_duplicates()
        connections = connections.dropna()

        connections = connections.to_dict(orient="list")

        del tmp, tmp1, tmp2, reactome, top_level

        return connections

    ###########################################################################

    # HPA to dict
    def HPA_to_gene_dict(self, HPA_jbio):

        HPA_jbio = pd.DataFrame(HPA_jbio)

        HPA_jbio["Gene"] = [re.sub(" ", "", x.upper()) for x in HPA_jbio["Gene"]]

        HPA_jbio = HPA_jbio.drop_duplicates()

        HPA_jbio["Gene synonym"] = HPA_jbio["Gene synonym"].str.split(", ")

        jdci = pd.DataFrame(
            {
                "names": list(set(HPA_jbio["Gene"])),
                "id": range(len(list(set(HPA_jbio["Gene"])))),
            }
        )

        jdci["id"] = [int(x) for x in jdci["id"]]

        HPA_jbio = pd.merge(
            HPA_jbio,
            jdci[["names", "id"]],
            left_on="Gene",
            right_on="names",
            how="left",
        )

        HPA_jbio = HPA_jbio.drop("names", axis=1)

        synonymes = []
        for x in tqdm(HPA_jbio["Gene synonym"]):
            if x == x:
                synonymes = synonymes + [y.upper() for y in x]

        from collections import Counter

        dup = Counter(synonymes)

        dup = pd.DataFrame(dup.items(), columns=["value", "count"])
        dup = dup[dup["count"] > 1]
        dup = dup[dup["value"].notnull()]

        to_exclude = list(HPA_jbio["Gene"]) + list(dup["value"])

        to_exclude = list(set([x.upper() for x in to_exclude]))

        poss_names = []
        for inx, syn in enumerate(tqdm(HPA_jbio["Gene synonym"])):
            if syn == syn:
                poss_names.append(
                    [x.upper() for x in syn if x.upper() not in to_exclude]
                    + [HPA_jbio["Gene"][inx].upper()]
                    + [HPA_jbio["Ensembl"][inx].upper()]
                )
            else:
                poss_names.append(
                    [HPA_jbio["Gene"][inx].upper()] + [HPA_jbio["Ensembl"][inx].upper()]
                )

        HPA_jbio["possible_names"] = poss_names

        gene_dictionary = pd.DataFrame(self.gene_dict).reset_index(drop=True)

        fetures_id = self.find_fetures_id(gene_dictionary, HPA_jbio["Gene"])

        gene_dictionary["id_HPA"] = None
        gene_dictionary["primary_HPA_genes"] = None

        for inx, gene in enumerate(tqdm(fetures_id["found_genes"])):
            idr = list(
                set(HPA_jbio["id"][HPA_jbio["Gene"] == fetures_id["found_genes"][inx]])
            )[0]
            gene_dictionary["id_HPA"][fetures_id["found_ids"][inx][0]] = idr
            gene_dictionary["primary_HPA_genes"][fetures_id["found_ids"][inx][0]] = gene

        fetures_id2 = self.find_fetures_list_id(
            gene_dictionary,
            HPA_jbio["possible_names"][
                HPA_jbio["Gene"].isin(list(fetures_id["not_found"]))
            ],
        )

        fetures_id2["found_genes_STR"] = [str(x) for x in fetures_id2["found_genes"]]
        HPA_jbio["possible_names_STR"] = [str(x) for x in HPA_jbio["possible_names"]]

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        for inx, _ in enumerate(tqdm(fetures_id2["found_genes_STR"])):
            idr = list(
                set(
                    HPA_jbio["id"][
                        HPA_jbio["possible_names_STR"]
                        == fetures_id2["found_genes_STR"][inx]
                    ]
                )
            )[0]

            gene_dictionary["id_HPA"][fetures_id2["found_ids"][inx][0]] = idr
            gene_dictionary["primary_HPA_genes"][fetures_id2["found_ids"][inx][0]] = (
                fetures_id2["found_genes"][inx]
            )

        gene_dictionary = pd.DataFrame(gene_dictionary)

        fetures_id2["not_found_STR"] = [str(x) for x in fetures_id2["not_found"]]

        for inx, gene in enumerate(tqdm(set(fetures_id2["not_found_STR"]))):

            idr = list(set(HPA_jbio["id"][HPA_jbio["possible_names_STR"] == gene]))[0]
            new_row = {col: [None] for col in gene_dictionary.columns}
            new_row["id_HPA"] = [idr]
            new_row["possible_names"] = [fetures_id2["not_found"][inx]]
            new_row["species"] = [["Homo sapiens"]]
            new_row["primary_HPA_genes"] = [fetures_id2["not_found"][inx]]

            gene_dictionary = pd.concat([gene_dictionary, pd.DataFrame(new_row)])

        gene_dictionary = gene_dictionary.reset_index(drop=True)
        gene_dictionary = gene_dictionary.to_dict(orient="list")

        HPA_jbio = HPA_jbio.drop("possible_names_STR", axis=1)
        HPA_jbio_dict = HPA_jbio.to_dict(orient="list")

        self.gene_dict = gene_dictionary

        return HPA_jbio_dict

    def specificity_prepare(self, HPA_jbio):

        HPA_jbio = pd.DataFrame(HPA_jbio)

        # cell specificity

        RNA_tissue = HPA_jbio[
            [
                "Gene",
                "RNA tissue specificity",
                "RNA tissue distribution",
                "RNA tissue specificity score",
                "RNA tissue specific nTPM",
                "id",
            ]
        ]
        RNA_tissue = RNA_tissue.dropna()
        RNA_tissue.columns = [
            "gene_name",
            "specificity",
            "distribution",
            "standarized_specificity_score",
            "nTPM",
            "id",
        ]
        nTPM = (
            RNA_tissue["nTPM"]
            .str.split(";", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("nTPM")
        )
        RNA_tissue = RNA_tissue.drop("nTPM", axis=1).join(nTPM)
        RNA_tissue[["name", "TPM"]] = RNA_tissue["nTPM"].str.split(
            ":", n=1, expand=True
        )
        RNA_tissue["name"] = RNA_tissue["name"].str.replace(r" \d+$", "", regex=True)

        RNA_tissue["TPM"] = [float(x) for x in RNA_tissue["TPM"]]
        RNA_tissue["log_TPM"] = np.log(RNA_tissue["TPM"] + 1)

        RNA_tissue["standarized_specificity_score"] = [
            float(x) for x in RNA_tissue["standarized_specificity_score"]
        ]
        RNA_tissue["log_standarized_specificity_score"] = np.log(
            RNA_tissue["standarized_specificity_score"] + 1
        )

        RNA_single_cell = HPA_jbio[
            [
                "Gene",
                "RNA single cell type specificity",
                "RNA single cell type distribution",
                "RNA single cell type specificity score",
                "RNA single cell type specific nTPM",
                "id",
            ]
        ]
        RNA_single_cell = RNA_single_cell.dropna()
        RNA_single_cell.columns = [
            "gene_name",
            "specificity",
            "distribution",
            "standarized_specificity_score",
            "nTPM",
            "id",
        ]
        nTPM = (
            RNA_single_cell["nTPM"]
            .str.split(";", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("nTPM")
        )
        RNA_single_cell = RNA_single_cell.drop("nTPM", axis=1).join(nTPM)
        RNA_single_cell[["name", "TPM"]] = RNA_single_cell["nTPM"].str.split(
            ":", n=1, expand=True
        )
        RNA_single_cell["name"] = RNA_single_cell["name"].str.replace(
            r" \d+$", "", regex=True
        )

        RNA_single_cell["TPM"] = [float(x) for x in RNA_single_cell["TPM"]]
        RNA_single_cell["log_TPM"] = np.log(RNA_single_cell["TPM"] + 1)

        RNA_single_cell["standarized_specificity_score"] = [
            float(x) for x in RNA_single_cell["standarized_specificity_score"]
        ]
        RNA_single_cell["log_standarized_specificity_score"] = np.log(
            RNA_single_cell["standarized_specificity_score"] + 1
        )

        RNA_cancer = HPA_jbio[
            [
                "Gene",
                "RNA cancer specificity",
                "RNA cancer distribution",
                "RNA cancer specificity score",
                "RNA cancer specific FPKM",
                "id",
            ]
        ]
        RNA_cancer = RNA_cancer.dropna()
        RNA_cancer.columns = [
            "gene_name",
            "specificity",
            "distribution",
            "standarized_specificity_score",
            "nTPM",
            "id",
        ]
        nTPM = (
            RNA_cancer["nTPM"]
            .str.split(";", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("nTPM")
        )
        RNA_cancer = RNA_cancer.drop("nTPM", axis=1).join(nTPM)
        RNA_cancer[["name", "TPM"]] = RNA_cancer["nTPM"].str.split(
            ":", n=1, expand=True
        )
        RNA_cancer["name"] = RNA_cancer["name"].str.replace(r" \d+$", "", regex=True)

        RNA_cancer["TPM"] = [float(x) for x in RNA_cancer["TPM"]]
        RNA_cancer["log_TPM"] = np.log(RNA_cancer["TPM"] + 1)

        RNA_cancer["standarized_specificity_score"] = [
            float(x) for x in RNA_cancer["standarized_specificity_score"]
        ]
        RNA_cancer["log_standarized_specificity_score"] = np.log(
            RNA_cancer["standarized_specificity_score"] + 1
        )

        RNA_brain = HPA_jbio[
            [
                "Gene",
                "RNA brain regional specificity",
                "RNA brain regional distribution",
                "RNA brain regional specificity score",
                "RNA brain regional specific nTPM",
                "id",
            ]
        ]
        RNA_brain = RNA_brain.dropna()
        RNA_brain.columns = [
            "gene_name",
            "specificity",
            "distribution",
            "standarized_specificity_score",
            "nTPM",
            "id",
        ]
        nTPM = (
            RNA_brain["nTPM"]
            .str.split(";", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("nTPM")
        )
        RNA_brain = RNA_brain.drop("nTPM", axis=1).join(nTPM)
        RNA_brain[["name", "TPM"]] = RNA_brain["nTPM"].str.split(":", n=1, expand=True)
        RNA_brain["name"] = RNA_brain["name"].str.replace(r" \d+$", "", regex=True)

        RNA_brain["TPM"] = [float(x) for x in RNA_brain["TPM"]]
        RNA_brain["log_TPM"] = np.log(RNA_brain["TPM"] + 1)

        RNA_brain["standarized_specificity_score"] = [
            float(x) for x in RNA_brain["standarized_specificity_score"]
        ]
        RNA_brain["log_standarized_specificity_score"] = np.log(
            RNA_brain["standarized_specificity_score"] + 1
        )

        RNA_blood = HPA_jbio[
            [
                "Gene",
                "RNA blood cell specificity",
                "RNA blood cell distribution",
                "RNA blood cell specificity score",
                "RNA blood cell specific nTPM",
                "id",
            ]
        ]
        RNA_blood = RNA_blood.dropna()
        RNA_blood.columns = [
            "gene_name",
            "specificity",
            "distribution",
            "standarized_specificity_score",
            "nTPM",
            "id",
        ]
        nTPM = (
            RNA_blood["nTPM"]
            .str.split(";", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("nTPM")
        )
        RNA_blood = RNA_blood.drop("nTPM", axis=1).join(nTPM)
        RNA_blood[["name", "TPM"]] = RNA_blood["nTPM"].str.split(":", n=1, expand=True)
        RNA_blood["name"] = RNA_blood["name"].str.replace(r" \d+$", "", regex=True)

        RNA_blood["TPM"] = [float(x) for x in RNA_blood["TPM"]]
        RNA_blood["log_TPM"] = np.log(RNA_blood["TPM"] + 1)

        RNA_blood["standarized_specificity_score"] = [
            float(x) for x in RNA_blood["standarized_specificity_score"]
        ]
        RNA_blood["log_standarized_specificity_score"] = np.log(
            RNA_blood["standarized_specificity_score"] + 1
        )

        RNA_blood_lineage = HPA_jbio[
            [
                "Gene",
                "RNA blood lineage specificity",
                "RNA blood lineage distribution",
                "RNA blood lineage specificity score",
                "RNA blood lineage specific nTPM",
                "id",
            ]
        ]
        RNA_blood_lineage = RNA_blood_lineage.dropna()
        RNA_blood_lineage.columns = [
            "gene_name",
            "specificity",
            "distribution",
            "standarized_specificity_score",
            "nTPM",
            "id",
        ]
        nTPM = (
            RNA_blood_lineage["nTPM"]
            .str.split(";", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("nTPM")
        )
        RNA_blood_lineage = RNA_blood_lineage.drop("nTPM", axis=1).join(nTPM)
        RNA_blood_lineage[["name", "TPM"]] = RNA_blood_lineage["nTPM"].str.split(
            ":", n=1, expand=True
        )
        RNA_blood_lineage["name"] = RNA_blood_lineage["name"].str.replace(
            r" \d+$", "", regex=True
        )

        RNA_blood_lineage["TPM"] = [float(x) for x in RNA_blood_lineage["TPM"]]
        RNA_blood_lineage["log_TPM"] = np.log(RNA_blood_lineage["TPM"] + 1)

        RNA_blood_lineage["standarized_specificity_score"] = [
            float(x) for x in RNA_blood_lineage["standarized_specificity_score"]
        ]
        RNA_blood_lineage["log_standarized_specificity_score"] = np.log(
            RNA_blood_lineage["standarized_specificity_score"] + 1
        )

        RNA_cell_line = HPA_jbio[
            [
                "Gene",
                "RNA cell line specificity",
                "RNA cell line distribution",
                "RNA cell line specificity score",
                "RNA cell line specific nTPM",
                "id",
            ]
        ]
        RNA_cell_line = RNA_cell_line.dropna()
        RNA_cell_line.columns = [
            "gene_name",
            "specificity",
            "distribution",
            "standarized_specificity_score",
            "nTPM",
            "id",
        ]
        nTPM = (
            RNA_cell_line["nTPM"]
            .str.split(";", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("nTPM")
        )
        RNA_cell_line = RNA_cell_line.drop("nTPM", axis=1).join(nTPM)
        RNA_cell_line[["name", "TPM"]] = RNA_cell_line["nTPM"].str.split(
            ":", n=1, expand=True
        )
        RNA_cell_line["name"] = RNA_cell_line["name"].str.replace(
            r" \d+$", "", regex=True
        )

        RNA_cell_line["TPM"] = [float(x) for x in RNA_cell_line["TPM"]]
        RNA_cell_line["log_TPM"] = np.log(RNA_cell_line["TPM"] + 1)

        RNA_cell_line["standarized_specificity_score"] = [
            float(x) for x in RNA_cell_line["standarized_specificity_score"]
        ]
        RNA_cell_line["log_standarized_specificity_score"] = np.log(
            RNA_cell_line["standarized_specificity_score"] + 1
        )

        RNA_mouse_brain_region = HPA_jbio[
            [
                "Gene",
                "RNA mouse brain regional specificity",
                "RNA mouse brain regional distribution",
                "RNA mouse brain regional specificity score",
                "RNA mouse brain regional specific nTPM",
                "id",
            ]
        ]
        RNA_mouse_brain_region = RNA_mouse_brain_region.dropna()
        RNA_mouse_brain_region.columns = [
            "gene_name",
            "specificity",
            "distribution",
            "standarized_specificity_score",
            "nTPM",
            "id",
        ]
        nTPM = (
            RNA_mouse_brain_region["nTPM"]
            .str.split(";", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("nTPM")
        )
        RNA_mouse_brain_region = RNA_mouse_brain_region.drop("nTPM", axis=1).join(nTPM)
        RNA_mouse_brain_region[["name", "TPM"]] = RNA_mouse_brain_region[
            "nTPM"
        ].str.split(":", n=1, expand=True)
        RNA_mouse_brain_region["name"] = RNA_mouse_brain_region["name"].str.replace(
            r" \d+$", "", regex=True
        )

        RNA_mouse_brain_region["TPM"] = [
            float(x) for x in RNA_mouse_brain_region["TPM"]
        ]
        RNA_mouse_brain_region["log_TPM"] = np.log(RNA_mouse_brain_region["TPM"] + 1)

        RNA_mouse_brain_region["standarized_specificity_score"] = [
            float(x) for x in RNA_mouse_brain_region["standarized_specificity_score"]
        ]
        RNA_mouse_brain_region["log_standarized_specificity_score"] = np.log(
            RNA_mouse_brain_region["standarized_specificity_score"] + 1
        )

        ###

        specificity_dict = {}

        specificity_dict["RNA_tissue"] = RNA_tissue[
            [
                "distribution",
                "standarized_specificity_score",
                "id",
                "name",
                "TPM",
                "log_TPM",
                "log_standarized_specificity_score",
            ]
        ].to_dict(orient="list")

        specificity_dict["RNA_single_cell"] = RNA_single_cell[
            [
                "distribution",
                "standarized_specificity_score",
                "id",
                "name",
                "TPM",
                "log_TPM",
                "log_standarized_specificity_score",
            ]
        ].to_dict(orient="list")

        specificity_dict["RNA_cancer"] = RNA_cancer[
            [
                "distribution",
                "standarized_specificity_score",
                "id",
                "name",
                "TPM",
                "log_TPM",
                "log_standarized_specificity_score",
            ]
        ].to_dict(orient="list")

        specificity_dict["RNA_brain"] = RNA_brain[
            [
                "distribution",
                "standarized_specificity_score",
                "id",
                "name",
                "TPM",
                "log_TPM",
                "log_standarized_specificity_score",
            ]
        ].to_dict(orient="list")

        specificity_dict["RNA_blood"] = RNA_blood[
            [
                "distribution",
                "standarized_specificity_score",
                "id",
                "name",
                "TPM",
                "log_TPM",
                "log_standarized_specificity_score",
            ]
        ].to_dict(orient="list")

        specificity_dict["RNA_blood_lineage"] = RNA_blood_lineage[
            [
                "distribution",
                "standarized_specificity_score",
                "id",
                "name",
                "TPM",
                "log_TPM",
                "log_standarized_specificity_score",
            ]
        ].to_dict(orient="list")

        specificity_dict["RNA_cell_line"] = RNA_cell_line[
            [
                "distribution",
                "standarized_specificity_score",
                "id",
                "name",
                "TPM",
                "log_TPM",
                "log_standarized_specificity_score",
            ]
        ].to_dict(orient="list")

        specificity_dict["RNA_mouse_brain_region"] = RNA_mouse_brain_region[
            [
                "distribution",
                "standarized_specificity_score",
                "id",
                "name",
                "TPM",
                "log_TPM",
                "log_standarized_specificity_score",
            ]
        ].to_dict(orient="list")

        ###

        # cellular location

        subcellular_location = HPA_jbio[["Gene", "Subcellular location", "id"]]
        subcellular_location = subcellular_location.dropna()
        subcellular_location.columns = ["gene_name", "location", "id"]
        subcellular_location["primary_location"] = "subcellular_location"

        secretome_location = HPA_jbio[["Gene", "Secretome location", "id"]]
        secretome_location = secretome_location.dropna()
        secretome_location.columns = ["gene_name", "location", "id"]
        secretome_location["primary_location"] = "secretome_location"

        subcellular_main_location = HPA_jbio[
            ["Gene", "Subcellular main location", "id"]
        ]
        subcellular_main_location = subcellular_main_location.dropna()
        subcellular_main_location.columns = ["gene_name", "location", "id"]
        subcellular_main_location["primary_location"] = "subcellular_location"

        subcellular_additional_location = HPA_jbio[
            ["Gene", "Subcellular additional location", "id"]
        ]
        subcellular_additional_location = subcellular_additional_location.dropna()
        subcellular_additional_location.columns = ["gene_name", "location", "id"]
        subcellular_additional_location["primary_location"] = "subcellular_location"

        location = pd.concat(
            [
                subcellular_location,
                secretome_location,
                subcellular_main_location,
                subcellular_additional_location,
            ]
        )

        locs = (
            location["location"]
            .str.split(",", expand=True)
            .stack()
            .reset_index(level=1, drop=True)
            .rename("location")
        )
        location = location.drop("location", axis=1).join(locs)
        location["location"] = location["location"].str.replace(
            r"^\s+|\s+$", "", regex=True
        )
        location["location"] = [
            x[0].upper() + x[1:].lower() for x in location["location"]
        ]
        location = location[["location", "id"]].drop_duplicates()
        location = location.reset_index(drop=True)

        location = location.to_dict(orient="list")

        specificity_dict["subcellular_location"] = location

        # blood markers

        blood_levels = HPA_jbio[
            [
                "Blood concentration - Conc. blood IM [pg/L]",
                "Blood concentration - Conc. blood MS [pg/L]",
                "id",
            ]
        ]
        blood_levels.columns = [
            "blood_concentration_IM[pg/L]",
            "blood_concentration_MS[pg/L]",
            "id",
        ]
        blood_levels = blood_levels.to_dict(orient="list")

        specificity_dict["blood_markers"] = blood_levels

        return specificity_dict

    ###########################################################################

    # DISEASES

    def diseases_to_gene_dict(self, disease_dict):

        disease_dict = pd.DataFrame(disease_dict)

        disease_dict["gene"] = [
            re.sub(" ", "", x.upper()) for x in disease_dict["gene"]
        ]

        disease_dict = disease_dict.drop_duplicates()

        jdci = pd.DataFrame(
            {
                "names": list(set(disease_dict["protein"])),
                "id": range(len(list(set(disease_dict["protein"])))),
            }
        )

        jdci["id"] = [int(x) for x in jdci["id"]]

        disease_dict = pd.merge(
            disease_dict,
            jdci[["names", "id"]],
            left_on="protein",
            right_on="names",
            how="left",
        )

        disease_dict = disease_dict.drop("names", axis=1)

        tmp_names = disease_dict[["gene", "protein", "id"]]

        tmp_names = disease_dict.groupby("protein").agg(lambda x: list(set(x.tolist())))

        tmp_names.reset_index(inplace=True)

        tmp_names["possible_names"] = tmp_names.apply(
            lambda row: list(
                set([y.upper() for y in row["gene"]] + [row["protein"].upper()])
            ),
            axis=1,
        )

        tmp_names["id"] = [x[0] for x in tmp_names["id"]]

        gene_dictionary = pd.DataFrame(self.gene_dict).reset_index(drop=True)

        fetures_id = self.find_fetures_list_id(
            gene_dictionary, tmp_names["possible_names"]
        )

        gene_dictionary["id_diseases"] = None
        gene_dictionary["primary_diseases_gene"] = None

        fetures_id["found_genes_STR"] = [str(x) for x in fetures_id["found_genes"]]
        tmp_names["possible_names_STR"] = [str(x) for x in tmp_names["possible_names"]]

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        for inx, _ in enumerate(tqdm(fetures_id["found_genes_STR"])):
            idr = list(
                set(
                    tmp_names["id"][
                        tmp_names["possible_names_STR"]
                        == fetures_id["found_genes_STR"][inx]
                    ]
                )
            )[0]

            gene_dictionary["id_diseases"][fetures_id["found_ids"][inx][0]] = idr
            gene_dictionary["primary_diseases_gene"][
                fetures_id["found_ids"][inx][0]
            ] = fetures_id["found_genes"][inx]

        gene_dictionary = pd.DataFrame(gene_dictionary)

        fetures_id["not_found_STR"] = [str(x) for x in fetures_id["not_found"]]

        for inx, gene in enumerate(tqdm(set(fetures_id["not_found_STR"]))):

            idr = list(set(tmp_names["id"][tmp_names["possible_names_STR"] == gene]))[0]
            new_row = {col: [None] for col in gene_dictionary.columns}
            new_row["id_diseases"] = [idr]
            new_row["possible_names"] = [fetures_id["not_found"][inx]]
            new_row["species"] = [["Homo sapiens"]]
            new_row["primary_diseases_gene"] = [fetures_id["not_found"][inx]]

            gene_dictionary = pd.concat([gene_dictionary, pd.DataFrame(new_row)])

        gene_dictionary = gene_dictionary.reset_index(drop=True)

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        disease_dict_jbio = disease_dict[["disease", "id"]]

        disease_dict_jbio = disease_dict_jbio.to_dict(orient="list")

        self.gene_dict = gene_dictionary

        return disease_dict_jbio

    ###########################################################################

    # VIRAL-DISEASES

    def viral_diseases_to_gene_dict(self, viral_dict):

        viral_dict = pd.DataFrame(viral_dict)

        viral_dict["Target_gene"] = [
            re.sub(" ", "", x.upper()) for x in viral_dict["Target_gene"]
        ]

        viral_dict = viral_dict.drop_duplicates()

        jdci = pd.DataFrame(
            {
                "names": list(set(viral_dict["Target_gene"])),
                "id": range(len(list(set(viral_dict["Target_gene"])))),
            }
        )

        jdci["id"] = [int(x) for x in jdci["id"]]

        viral_dict = pd.merge(
            viral_dict,
            jdci[["names", "id"]],
            left_on="Target_gene",
            right_on="names",
            how="left",
        )

        viral_dict = viral_dict.drop("names", axis=1)

        # temporary possible_names
        tmp_names = viral_dict[["GeneAlias", "Target_gene", "Protein_class", "id"]]

        tmp_names = tmp_names.groupby("Target_gene").agg(
            lambda x: list(set(x.tolist()))
        )

        tmp_names.reset_index(inplace=True)

        tmp_names["GeneAlias"] = [x[0] for x in tmp_names["GeneAlias"]]

        tmp_names["GeneAlias"] = tmp_names["GeneAlias"].str.split("; ")

        tmp_names["id"] = [x[0] for x in tmp_names["id"]]

        tmp_names["Protein_class"] = [x[0] for x in tmp_names["Protein_class"]]

        synonymes = []
        for x in tqdm(tmp_names["GeneAlias"]):
            if x == x:
                synonymes = synonymes + x

        from collections import Counter

        dup = Counter(synonymes)

        dup = pd.DataFrame(dup.items(), columns=["value", "count"])
        dup = dup[dup["count"] > 1]
        dup = dup[dup["value"].notnull()]

        to_exclude = list(viral_dict["Target_gene"]) + list(dup["value"])

        to_exclude = list(set([x.upper() for x in to_exclude]))

        poss_names = []
        for inx, syn in enumerate(tqdm(tmp_names["GeneAlias"])):
            if syn == syn:
                if tmp_names["Protein_class"][inx] == tmp_names["Protein_class"][inx]:
                    poss_names.append(
                        [x.upper() for x in syn if x.upper() not in to_exclude]
                        + [tmp_names["Target_gene"][inx].upper()]
                        + [tmp_names["Protein_class"][inx].upper()]
                    )
                else:
                    poss_names.append(
                        [x.upper() for x in syn if x.upper() not in to_exclude]
                        + [tmp_names["Target_gene"][inx].upper()]
                    )

            else:
                if tmp_names["Protein_class"][inx] == tmp_names["Protein_class"][inx]:
                    poss_names.append(
                        [tmp_names["Target_gene"][inx].upper()]
                        + [tmp_names["Protein_class"][inx].upper()]
                    )
                else:
                    poss_names.append([tmp_names["Target_gene"][inx].upper()])

        tmp_names["possible_names"] = poss_names

        gene_dictionary = pd.DataFrame(self.gene_dict).reset_index(drop=True)

        fetures_id = self.find_fetures_id(
            gene_dictionary, list(set(tmp_names["Target_gene"]))
        )

        gene_dictionary["id_viral_diseases"] = None
        gene_dictionary["primary_viral_diseases_genes"] = None

        for inx, gene in enumerate(tqdm(fetures_id["found_genes"])):
            idr = list(
                set(
                    tmp_names["id"][
                        tmp_names["Target_gene"] == fetures_id["found_genes"][inx]
                    ]
                )
            )[0]
            gene_dictionary["id_viral_diseases"][fetures_id["found_ids"][inx][0]] = idr
            gene_dictionary["primary_viral_diseases_genes"][
                fetures_id["found_ids"][inx][0]
            ] = gene

        fetures_id2 = self.find_fetures_list_id(
            gene_dictionary,
            tmp_names["possible_names"][
                tmp_names["Target_gene"].isin(list(fetures_id["not_found"]))
            ],
        )

        fetures_id2["found_genes_STR"] = [str(x) for x in fetures_id2["found_genes"]]
        tmp_names["possible_names_STR"] = [str(x) for x in tmp_names["possible_names"]]

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        for inx, _ in enumerate(tqdm(fetures_id2["found_genes_STR"])):
            idr = list(
                set(
                    tmp_names["id"][
                        tmp_names["possible_names_STR"]
                        == fetures_id2["found_genes_STR"][inx]
                    ]
                )
            )[0]

            gene_dictionary["id_viral_diseases"][fetures_id2["found_ids"][inx][0]] = idr
            gene_dictionary["primary_viral_diseases_genes"][
                fetures_id2["found_ids"][inx][0]
            ] = fetures_id2["found_genes"][inx]

        gene_dictionary = pd.DataFrame(gene_dictionary)

        fetures_id2["not_found_STR"] = [str(x) for x in fetures_id2["not_found"]]

        for inx, gene in enumerate(tqdm(set(fetures_id2["not_found_STR"]))):

            idr = list(set(tmp_names["id"][tmp_names["possible_names_STR"] == gene]))[0]
            new_row = {col: [None] for col in gene_dictionary.columns}
            new_row["id_viral_diseases"] = [idr]
            new_row["possible_names"] = [fetures_id2["not_found"][inx]]
            new_row["species"] = [["Homo sapiens"]]
            new_row["primary_viral_diseases_genes"] = [fetures_id2["not_found"][inx]]

            gene_dictionary = pd.concat([gene_dictionary, pd.DataFrame(new_row)])

        gene_dictionary = gene_dictionary.reset_index(drop=True)

        gene_dictionary = gene_dictionary.to_dict(orient="list")
        viral_dict_jbio = viral_dict[["virus", "group", "id"]]
        viral_dict_jbio = viral_dict_jbio.to_dict(orient="list")

        self.gene_dict = gene_dictionary

        return viral_dict_jbio

    # KEGG

    def kegg_to_gene_dict(self, kegg_jbio):

        kegg_jbio = pd.DataFrame(kegg_jbio)

        kegg_jbio = kegg_jbio.explode("gene").reset_index(drop=True)

        kegg_jbio["gene"] = [re.sub(" ", "", x.upper()) for x in kegg_jbio["gene"]]

        kegg_jbio = kegg_jbio.drop_duplicates()

        kegg_jbio = kegg_jbio.reset_index(drop=True)

        # rm non human entitis
        list_to_rm_KEGG = [
            "Viral",
            "Mycobacterium",
            "HIV-1",
            "virus",
            "fly",
            "plant",
            "yeast",
            "animal",
            "Caulobacter",
            "Vibrio cholerae",
            "Pseudomonas aeruginosa",
            "Escherichia coli",
            "worm",
            "antenna proteins",
        ]

        bacteria_names_latin = [
            "Escherichia coli",
            "Staphylococcus aureus",
            "Bacillus subtilis",
            "Mycobacterium tuberculosis",
            "Helicobacter pylori",
            "Clostridium difficile",
            "Salmonella enterica",
            "Lactobacillus acidophilus",
            "Pseudomonas aeruginosa",
            "Listeria monocytogenes",
            "Vibrio cholerae",
            "Mycoplasma pneumoniae",
            "Treponema pallidum",
            "Chlamydia trachomatis",
            "Borrelia burgdorferi",
            "Yersinia pestis",
            "Neisseria meningitidis",
            "Enterococcus faecalis",
            "Streptococcus pyogenes",
            "Campylobacter jejuni",
            "Corynebacterium diphtheriae",
            "Methanobrevibacter smithii",
            "Acetobacter aceti",
            "Lactococcus lactis",
            "Bacteroides fragilis",
            "Rhizobium leguminosarum",
            "Agrobacterium tumefaciens",
            "Helicobacter pylori",
            "Clostridium botulinum",
            "Bacillus anthracis",
            "Borrelia burgdorferi",
            "Chlamydia pneumoniae",
            "Legionella pneumophila",
            "Cyanobacterium Prochlorococcus",
            "Thermus aquaticus",
            "Deinococcus radiodurans",
            "Streptomyces coelicolor",
            "Shigella flexneri",
            "Chlorobium tepidum",
            "Lactobacillus casei",
            "Micrococcus luteus",
            "Spirochaeta africana",
            "Geobacter sulfurreducens",
            "Thermotoga maritima",
            "Verrucomicrobium spinosum",
            "Prevotella bryantii",
            "Desulfovibrio vulgaris",
            "Halobacterium salinarum",
            "Rickettsia prowazekii",
            "Leptospira interrogans",
            "Francisella tularensis",
            "Bacteroides thetaiotaomicron",
            "Streptococcus mutans",
            "Thermotoga neapolitana",
            "Deinococcus geothermalis",
            "Rhodopseudomonas palustris",
            "Bifidobacterium longum",
            "Candidatus Carsonella ruddii",
            "Magnetospirillum magneticum",
            "Desulforudis audaxviator",
            "Myxococcus xanthus",
            "Methanosarcina barkeri",
            "Propionibacterium acnes",
            "Nitrosomonas europaea",
            "Clostridium acetobutylicum",
            "Buchnera aphidicola",
            "Ruminococcus albus",
            "Chlorobaculum tepidum",
            "Aquifex aeolicus",
            "Shewanella oneidensis",
            "Lactococcus garvieae",
            "Mycoplasma genitalium",
            "Mycoplasma gallisepticum",
            "Thermus thermophilus",
            "Stenotrophomonas maltophilia",
            "Anaplasma marginale",
            "Treponema denticola",
            "Leptospira biflexa",
            "Vibrio fischeri",
            "Caulobacter crescentus",
            "Bartonella henselae",
            "Brucella abortus",
            "Rickettsia rickettsii",
            "Flavobacterium johnsoniae",
            "Candidatus Sulcia muelleri",
            "Escherichia coli O157:H7",
            "Aeromonas hydrophila",
            "Pseudomonas fluorescens",
            "Caulobacter vibrioides",
            "Xanthomonas campestris",
            "Legionella longbeachae",
            "Bordetella pertussis",
            "Coxiella burnetii",
            "Nitrosomonas eutropha",
            "Bacillus cereus",
            "Bifidobacterium adolescentis",
            "Brucella melitensis",
            "Yersinia enterocolitica",
            "Verrucomicrobium sp.",
            "Geobacter metallireducens",
            "Desulfovibrio desulfuricans",
            "Salmonella typhi",
            "Pseudomonas putida",
            "Chlamydia suis",
            "Rickettsia typhi",
            "Leptospira borgpetersenii",
            "Rhodopirellula baltica",
        ]

        yeast_and_candida_names_latin = [
            "Saccharomyces cerevisiae",
            "Candida albicans",
            "Saccharomyces pastorianus",
            "Cryptococcus neoformans",
            "Kluyveromyces lactis",
            "Debaryomyces hansenii",
            "Pichia pastoris",
            "Candida glabrata",
            "Candida krusei",
            "Yarrowia lipolytica",
            "Candida parapsilosis",
            "Saccharomyces bayanus",
            "Saccharomyces mikatae",
            "Saccharomyces paradoxus",
            "Candida tropicalis",
            "Pichia stipitis",
            "Saccharomyces kudriavzevii",
            "Candida utilis",
            "Candida lusitaniae",
            "Pichia methanolica",
            "Candida guilliermondii",
            "Candida auris",
            "Candida rugosa",
            "Candida kefyr",
            "Schizosaccharomyces pombe",
            "Candida zeylanoides",
            "Zygosaccharomyces bailii",
            "Hanseniaspora uvarum",
            "Issatchenkia orientalis",
            "Brettanomyces bruxellensis",
            "Pichia guilliermondii",
            "Candida famata",
            "Candida milleri",
            "Candida pelliculosa",
            "Candida vini",
            "Candida viswanathii",
            "Candida intermedia",
            "Saccharomycodes ludwigii",
            "Lodderomyces elongisporus",
            "Kluyveromyces marxianus",
            "Candida stellimalicola",
            "Metschnikowia pulcherrima",
            "Pichia jadinii",
            "Candida haemulonii",
            "Wickerhamomyces anomalus",
            "Candida silvicultrix",
            "Kazachstania africana",
            "Candida sake",
            "Candida dubliniensis",
            "Debaryomyces fabryi",
            "Candida maltosa",
            "Candida orthopsilosis",
            "Yamadazyma terventina",
            "Kazachstania servazzii",
            "Pichia membranifaciens",
            "Pichia kudriavzevii",
            "Lipomyces starkeyi",
            "Candida castellii",
            "Candida diddensiae",
            "Candida norvegensis",
            "Candida wickerhamii",
            "Candida fermentati",
            "Candida solani",
            "Candida pararugosa",
            "Candida rancensis",
            "Candida maris",
            "Candida incommunis",
            "Saccharomyces exiguus",
            "Candida oleophila",
            "Candida sorbophila",
            "Candida ethanolica",
            "Candida valdiviana",
            "Candida californica",
            "Candida membranifaciens",
            "Kazachstania heterogenica",
            "Candida azyma",
            "Candida blattae",
            "Candida athensensis",
            "Candida nivariensis",
            "Kazachstania unispora",
            "Candida pseudohaemulonii",
            "Candida jeffriesii",
            "Candida silvae",
            "Candida orthofermentans",
            "Candida sojae",
            "Kazachstania exigua",
            "Candida tsuchiyae",
            "Candida macedoniensis",
            "Candida lactis",
            "Candida cellae",
            "Candida deserticola",
            "Candida viswanathii",
            "Candida friedrichii",
            "Candida crustulenta",
            "Candida musae",
            "Candida robnettiae",
            "Candida dutilhii",
            "Candida langeronii",
            "Candida monacensis",
            "Candida vaughaniae",
            "Candida spearei",
            "Candida margaritae",
            "Candida lundensis",
            "Candida catenulata",
            "Candida sojana",
            "Candida meyerae",
            "Candida thailandica",
            "Candida idiomarina",
            "Candida vartiovaarae",
            "Candida hanlinii",
            "Candida colliculosa",
            "Candida liburnica",
            "Candida holmii",
            "Candida americana",
            "Candida ranongensis",
            "Candida slooffiae",
            "Candida margarethae",
            "Candida taylorii",
            "Candida kluyveri",
            "Candida castellanii",
            "Candida europaea",
            "Candida floricola",
            "Candida lambica",
            "Candida surugaensis",
            "Candida oregonensis",
            "Candida hetfieldiae",
            "Candida wissei",
            "Candida dairensis",
            "Candida friedrichii",
            "Candida psychrophila",
            "Candida mesorugosa",
            "Candida stellimalicola",
            "Candida heliconiae",
            "Candida fukuyamaensis",
            "Candida odintsovae",
            "Candida phangngensis",
            "Candida peltatoides",
            "Candida tsukubaensis",
            "Candida olei",
            "Candida temperata",
            "Candida coipomoensis",
            "Candida ishiwadae",
            "Candida subtropicalis",
            "Candida scottii",
            "Candida cruzei",
            "Candida aaseri",
            "Candida aquaticus",
            "Candida diogoi",
            "Candida fluvialitis",
            "Candida heliconiae",
            "Candida maltosa",
            "Candida monilioides",
            "Candida oleophila",
            "Candida parapsilosis",
        ]

        list_to_rm_KEGG = (
            list_to_rm_KEGG + bacteria_names_latin + yeast_and_candida_names_latin
        )

        inx_list = []
        for inx in tqdm(kegg_jbio.index):
            for i in list_to_rm_KEGG:
                if i in str(kegg_jbio["3rd"][inx]) and "Human Diseases" not in str(
                    kegg_jbio["1st"][inx]
                ):
                    inx_list.append(inx)
                    break

        kegg_jbio = kegg_jbio.drop(index=inx_list)

        kegg_jbio = kegg_jbio[
            ~kegg_jbio["3rd"].isin(
                [
                    "Function unknown",
                    "General function prediction only",
                    "Unclassified viral proteins",
                    "Others",
                    "Enzymes with EC numbers",
                    "Domain-containing proteins not elsewhere classified",
                ]
            )
        ]

        kegg_jbio = kegg_jbio.reset_index(drop=True)

        jdci = pd.DataFrame(
            {
                "names": list(set(kegg_jbio["gene"])),
                "id": range(len(list(set(kegg_jbio["gene"])))),
            }
        )

        jdci["id"] = [int(x) for x in jdci["id"]]

        kegg_jbio = pd.merge(
            kegg_jbio,
            jdci[["names", "id"]],
            left_on="gene",
            right_on="names",
            how="left",
        )

        kegg_jbio = kegg_jbio.drop("names", axis=1)

        gene_dictionary = pd.DataFrame(self.gene_dict).reset_index(drop=True)

        fetures_id = self.find_fetures_id(gene_dictionary, list(set(kegg_jbio["gene"])))

        gene_dictionary["id_KEGG"] = None
        gene_dictionary["primary_reactome_KEGG"] = None

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        for inx, gene in enumerate(tqdm(fetures_id["found_genes"])):
            idr = list(
                set(
                    kegg_jbio["id"][kegg_jbio["gene"] == fetures_id["found_genes"][inx]]
                )
            )[0]
            gene_dictionary["id_KEGG"][fetures_id["found_ids"][inx][0]] = idr
            gene_dictionary["primary_reactome_KEGG"][
                fetures_id["found_ids"][inx][0]
            ] = gene

        kegg_jbio = kegg_jbio[["1st", "2nd", "3rd", "name", "id"]]

        kegg_jbio = kegg_jbio.to_dict(orient="list")

        self.gene_dict = gene_dictionary

        return kegg_jbio

    ##GO-TERM

    def go_to_gene_dict(self, go_term_jbio):

        go_term = pd.DataFrame(go_term_jbio["metadata"])

        go_term = go_term.drop_duplicates()

        go_term["gene_name"] = [x.upper() for x in go_term["gene_name"]]
        jdci = pd.DataFrame(
            {
                "names": list(set(go_term["gene_name"])),
                "id": range(len(list(set(go_term["gene_name"])))),
            }
        )

        jdci["id"] = [int(x) for x in jdci["id"]]

        go_term = pd.merge(
            go_term,
            jdci[["names", "id"]],
            left_on="gene_name",
            right_on="names",
            how="left",
        )

        go_term = go_term.drop("names", axis=1)

        gene_dictionary = pd.DataFrame(self.gene_dict).reset_index(drop=True)

        fetures_id = self.find_fetures_id(
            gene_dictionary, list(set(go_term["gene_name"]))
        )

        gene_dictionary["id_GO"] = None
        gene_dictionary["primary_GO_gene"] = None

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        for inx, gene in enumerate(tqdm(fetures_id["found_genes"])):
            idr = list(
                set(
                    go_term["id"][
                        go_term["gene_name"] == fetures_id["found_genes"][inx]
                    ]
                )
            )[0]

            gene_dictionary["id_GO"][fetures_id["found_ids"][inx][0]] = idr
            gene_dictionary["primary_GO_gene"][fetures_id["found_ids"][inx][0]] = gene

        gene_dictionary = pd.DataFrame(gene_dictionary)

        for gene in tqdm(set(fetures_id["not_found"])):

            idr = list(set(go_term["id"][go_term["gene_name"] == gene]))[0]
            new_row = {col: [None] for col in gene_dictionary.columns}
            new_row["id_GO"] = [idr]
            new_row["possible_names"] = [[gene]]
            new_row["species"] = [
                list(set(go_term["species"][go_term["gene_name"] == gene]))
            ]
            new_row["primary_GO_gene"] = [gene]

            gene_dictionary = pd.concat([gene_dictionary, pd.DataFrame(new_row)])

        gene_dictionary = gene_dictionary.reset_index(drop=True)

        go_term = go_term.to_dict(orient="list")

        go_term_jbio["metadata"] = go_term

        self.gene_dict = gene_dictionary

        return go_term_jbio

    def go_adjustment(self, go_term_jbio):

        go = pd.DataFrame(go_term_jbio["metadata"])

        go = go[["connection", "GO_id", "species", "id"]]

        go2 = pd.DataFrame(go_term_jbio["connections"])
        go2 = go2[go2["obsolete"] is False]

        go_names = go2[["GO_id", "name", "name_space", "definition"]]
        go_names = go_names.drop_duplicates()

        go_names["tmp"] = [x.upper() for x in go_names["name_space"]]

        name_mapping = dict(
            zip(
                ["BIOLOGICAL_PROCESS", "CELLULAR_COMPONENT", "MOLECULAR_FUNCTION"],
                ["BP : ", "CC : ", "MF : "],
            )
        )

        go_names["tmp"] = go_names["tmp"].map(name_mapping)

        go_names["name"] = go_names["tmp"] + go_names["name"]

        go_names.pop("tmp")

        hierarchy = go2[
            [
                "GO_id",
                "is_a_ids",
                "part_of_ids",
                "has_part_ids",
                "regulates_ids",
                "negatively_regulates_ids",
                "positively_regulates_ids",
            ]
        ]

        hierarchy = hierarchy[
            ~hierarchy["GO_id"].isin(
                list(
                    go_names["GO_id"][
                        go_names["name"].isin(list(set(go_names["name_space"])))
                    ]
                )
            )
        ]

        hierarchy = hierarchy.explode("is_a_ids")
        hierarchy = hierarchy.explode("part_of_ids")
        hierarchy = hierarchy.explode("has_part_ids")
        hierarchy = hierarchy.explode("regulates_ids")
        hierarchy = hierarchy.explode("negatively_regulates_ids")
        hierarchy = hierarchy.explode("positively_regulates_ids")

        hierarchy = hierarchy.drop_duplicates()

        go_dict = {
            "gene_info": go.to_dict(orient="list"),
            "go_names": go_names.to_dict(orient="list"),
            "hierarchy": hierarchy.to_dict(orient="list"),
        }

        del go2, go, name_mapping, go_term_jbio, hierarchy, go_names

        return go_dict

    # INTACT

    def intact_to_gene_dict(self, IntAct_dict):

        IntAct_dict_tmp = pd.DataFrame(IntAct_dict["gene_product"])

        IntAct_dict_tmp = IntAct_dict_tmp.reset_index(drop=True)
        IntAct_dict_tmp = IntAct_dict_tmp[
            IntAct_dict_tmp["species_1"].isin(
                ["Homo sapiens", "Mus musculus", "Rattus norvegicus (Rat)"]
            )
        ]
        IntAct_dict_tmp = IntAct_dict_tmp[
            IntAct_dict_tmp["species_2"].isin(
                ["Homo sapiens", "Mus musculus", "Rattus norvegicus (Rat)"]
            )
        ]
        IntAct_dict_tmp["species_1"][
            IntAct_dict_tmp["species_1"] == "Rattus norvegicus (Rat)"
        ] = "Rattus norvegicus"
        IntAct_dict_tmp["species_2"][
            IntAct_dict_tmp["species_2"] == "Rattus norvegicus (Rat)"
        ] = "Rattus norvegicus"

        IntAct_dict_tmp["gene_name_1"] = [
            x.upper() for x in IntAct_dict_tmp["gene_name_1"]
        ]
        IntAct_dict_tmp["gene_name_2"] = [
            x.upper() for x in IntAct_dict_tmp["gene_name_2"]
        ]

        genes = list(IntAct_dict_tmp["gene_name_1"]) + list(
            IntAct_dict_tmp["gene_name_2"]
        )

        jdci = pd.DataFrame(
            {"names": list(set(genes)), "id": range(len(list(set(genes))))}
        )

        jdci["id"] = [int(x) for x in jdci["id"]]

        IntAct_dict_tmp = pd.merge(
            IntAct_dict_tmp,
            jdci[["names", "id"]],
            left_on="gene_name_1",
            right_on="names",
            how="left",
        )
        IntAct_dict_tmp = IntAct_dict_tmp.drop("names", axis=1)
        IntAct_dict_tmp = IntAct_dict_tmp.rename(columns={"id": "id_1"})

        IntAct_dict_tmp = pd.merge(
            IntAct_dict_tmp,
            jdci[["names", "id"]],
            left_on="gene_name_2",
            right_on="names",
            how="left",
        )
        IntAct_dict_tmp = IntAct_dict_tmp.drop("names", axis=1)
        IntAct_dict_tmp = IntAct_dict_tmp.rename(columns={"id": "id_2"})

        jdci = pd.merge(
            jdci,
            IntAct_dict_tmp[["species_1", "species_2", "id_1"]],
            left_on="id",
            right_on="id_1",
            how="left",
        )
        jdci = pd.merge(
            jdci,
            IntAct_dict_tmp[["species_1", "species_2", "id_2"]],
            left_on="id",
            right_on="id_2",
            how="left",
        )
        jdci = jdci.drop_duplicates()

        jdci = jdci.reset_index(drop=True)

        species = []
        for inx, _ in enumerate(tqdm(jdci["id"])):
            species.append(
                list(
                    set(
                        [
                            x
                            for x in [jdci["species_1_x"][inx]]
                            + [jdci["species_2_x"][inx]]
                            + [jdci["species_1_y"][inx]]
                            + [jdci["species_2_y"][inx]]
                            if x == x
                        ]
                    )
                )
            )

        jdci["species"] = species

        gene_dictionary = pd.DataFrame(self.gene_dict)

        fetures_id = self.find_fetures_id(gene_dictionary, list(set(jdci["names"])))

        gene_dictionary["id_IntAct"] = None
        gene_dictionary["primary_IntAct_gene"] = None

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        for inx, gene in enumerate(tqdm(fetures_id["found_genes"])):
            idr = list(
                set(jdci["id"][jdci["names"] == fetures_id["found_genes"][inx]])
            )[0]

            gene_dictionary["id_IntAct"][fetures_id["found_ids"][inx][0]] = idr
            gene_dictionary["primary_IntAct_gene"][
                fetures_id["found_ids"][inx][0]
            ] = gene

        gene_dictionary = pd.DataFrame(gene_dictionary)

        for gene in tqdm(set(fetures_id["not_found"])):

            idr = list(set(jdci["id"][jdci["names"] == gene]))[0]
            new_row = {col: [None] for col in gene_dictionary.columns}
            new_row["id_IntAct"] = [idr]
            new_row["possible_names"] = [[gene]]
            tmp_spec = list(jdci["species"][jdci["names"] == gene])
            if isinstance(tmp_spec[0], list):
                t = []
                for i in tmp_spec:
                    t = t + i

                new_row["species"] = [list(set(t))]

            else:
                new_row["species"] = tmp_spec
            new_row["primary_IntAct_gene"] = [gene]

            gene_dictionary = pd.concat([gene_dictionary, pd.DataFrame(new_row)])

        gene_dictionary = gene_dictionary.reset_index(drop=True)

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        IntAct_dict_tmp = IntAct_dict_tmp.reset_index(drop=True)

        IntAct_dict_tmp = IntAct_dict_tmp.to_dict(orient="list")

        IntAct_dict_tmp2 = pd.DataFrame(IntAct_dict["non_gene_product"])

        IntAct_dict_tmp2 = pd.merge(
            IntAct_dict_tmp2,
            jdci[["names", "id"]],
            left_on="gene_name_1",
            right_on="names",
            how="left",
        )
        IntAct_dict_tmp2 = IntAct_dict_tmp2.drop("names", axis=1)
        IntAct_dict_tmp2 = IntAct_dict_tmp2.rename(columns={"id": "id_1"})

        IntAct_dict_tmp2 = pd.merge(
            IntAct_dict_tmp2,
            jdci[["names", "id"]],
            left_on="gene_name_2",
            right_on="names",
            how="left",
        )
        IntAct_dict_tmp2 = IntAct_dict_tmp2.drop("names", axis=1)
        IntAct_dict_tmp2 = IntAct_dict_tmp2.rename(columns={"id": "id_2"})

        IntAct_dict_tmp2 = IntAct_dict_tmp2.reset_index(drop=True)

        IntAct_dict_tmp2 = IntAct_dict_tmp2.to_dict(orient="list")

        IntAct_dict["gene_product"] = IntAct_dict_tmp

        IntAct_dict["non_gene_product"] = IntAct_dict_tmp2

        self.gene_dict = gene_dictionary

        return IntAct_dict

    def gene_interactome_prepare_IntAct(self, IntAct_dict):

        intact_dict_tmp = pd.DataFrame(IntAct_dict["gene_product"])

        intact_dict_tmp = intact_dict_tmp[
            intact_dict_tmp["species_1"] == intact_dict_tmp["species_2"]
        ]

        intact_dict_tmp = intact_dict_tmp[
            [
                "interaction_type",
                "gene_1_biological_role",
                "interactor_type_1",
                "gene_2_biological_role",
                "interactor_type_2",
                "id_1",
                "id_2",
                "species_1",
                "source",
            ]
        ]

        intact_dict_tmp.columns = [
            "interaction_type",
            "gene_1_biological_role",
            "interactor_type_1",
            "gene_2_biological_role",
            "interactor_type_2",
            "id_1",
            "id_2",
            "species",
            "source",
        ]

        IntAct_dict["gene_product"] = intact_dict_tmp.to_dict(orient="list")

        intact_dict_tmp = pd.DataFrame(IntAct_dict["non_gene_product"])

        intact_dict_tmp = intact_dict_tmp[
            [
                "interaction_type",
                "gene_name_1",
                "gene_1_biological_role",
                "interactor_type_1",
                "gene_name_2",
                "gene_2_biological_role",
                "interactor_type_2",
                "id_1",
                "id_2",
                "species_1",
                "source",
            ]
        ]

        intact_dict_tmp.columns = [
            "interaction_type",
            "gene_1_biological_role",
            "gene_name_1",
            "interactor_type_1",
            "gene_name_2",
            "gene_2_biological_role",
            "interactor_type_2",
            "id_1",
            "id_2",
            "species",
            "source",
        ]

        IntAct_dict["non_gene_product"] = intact_dict_tmp.to_dict(orient="list")

        return IntAct_dict

    # STRING

    def string_to_gene_dict(self, string_dict):

        string_annotations = pd.DataFrame(string_dict["metadata"])
        string_annotations = string_annotations.reset_index(drop=True)

        string_annotations["preferred_name"] = [
            re.sub("_RAT", "", x.upper()) for x in string_annotations["preferred_name"]
        ]

        jdci = pd.DataFrame(
            {
                "names": list(set(string_annotations["preferred_name"])),
                "id": range(len(list(set(string_annotations["preferred_name"])))),
            }
        )

        jdci["id"] = [int(x) for x in jdci["id"]]

        string_annotations = pd.merge(
            string_annotations,
            jdci[["names", "id"]],
            left_on="preferred_name",
            right_on="names",
            how="left",
        )

        string_annotations = string_annotations.drop("names", axis=1)

        gene_dictionary = pd.DataFrame(self.gene_dict).reset_index(drop=True)

        fetures_id = self.find_fetures_id(
            gene_dictionary, list(set(string_annotations["preferred_name"]))
        )

        gene_dictionary["id_STRING"] = None
        gene_dictionary["primary_STRING_gene"] = None

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        for inx, gene in enumerate(tqdm(fetures_id["found_genes"])):
            idr = list(
                set(
                    string_annotations["id"][
                        string_annotations["preferred_name"]
                        == fetures_id["found_genes"][inx]
                    ]
                )
            )[0]

            gene_dictionary["id_STRING"][fetures_id["found_ids"][inx][0]] = idr
            gene_dictionary["primary_STRING_gene"][
                fetures_id["found_ids"][inx][0]
            ] = gene

        gene_dictionary = pd.DataFrame(gene_dictionary)

        for gene in tqdm(set(fetures_id["not_found"])):

            idr = list(
                set(
                    string_annotations["id"][
                        string_annotations["preferred_name"] == gene
                    ]
                )
            )[0]
            new_row = {col: [None] for col in gene_dictionary.columns}
            new_row["id_STRING"] = [idr]
            new_row["possible_names"] = [[gene]]
            new_row["species"] = list(
                string_annotations["species"][
                    string_annotations["preferred_name"] == gene
                ]
            )
            new_row["primary_STRING_gene"] = [gene]

            gene_dictionary = pd.concat([gene_dictionary, pd.DataFrame(new_row)])

        gene_dictionary = gene_dictionary.reset_index(drop=True)

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        string_annotations = string_annotations.to_dict(orient="list")

        string_dict["metadata"] = string_annotations

        self.gene_dict = gene_dictionary

        return string_dict

    def gene_interactome_prepare_STRING(self, string_dict):

        string_meta = pd.DataFrame(string_dict["metadata"])
        string = pd.DataFrame(string_dict["ppi"])

        string_meta = string_meta[["preferred_name", "id"]].drop_duplicates()

        name_mapping = dict(
            zip(list(string_meta["preferred_name"]), list(string_meta["id"]))
        )

        string["protein1"] = string["protein1"].map(name_mapping)
        string["protein2"] = string["protein2"].map(name_mapping)

        del name_mapping

        string["source"] = [[]] * len(string["protein1"])

        string.loc[string["neighborhood"] > 0, "source"] = string.loc[
            string["neighborhood"] > 0, "source"
        ].apply(lambda x: x + ["neighborhood"])

        string = string.drop("neighborhood", axis=1)

        string.loc[string["neighborhood_transferred"] > 0, "source"] = string.loc[
            string["neighborhood_transferred"] > 0, "source"
        ].apply(lambda x: x + ["neighborhood_transferred"])

        string = string.drop("neighborhood_transferred", axis=1)

        string.loc[string["fusion"] > 0, "source"] = string.loc[
            string["fusion"] > 0, "source"
        ].apply(lambda x: x + ["fusion"])

        string = string.drop("fusion", axis=1)

        string.loc[string["cooccurence"] > 0, "source"] = string.loc[
            string["cooccurence"] > 0, "source"
        ].apply(lambda x: x + ["cooccurence"])

        string = string.drop("cooccurence", axis=1)

        string.loc[string["homology"] > 0, "source"] = string.loc[
            string["homology"] > 0, "source"
        ].apply(lambda x: x + ["homology"])

        string = string.drop("homology", axis=1)

        string.loc[string["coexpression"] > 0, "source"] = string.loc[
            string["coexpression"] > 0, "source"
        ].apply(lambda x: x + ["coexpression"])

        string = string.drop("coexpression", axis=1)

        string.loc[string["coexpression_transferred"] > 0, "source"] = string.loc[
            string["coexpression_transferred"] > 0, "source"
        ].apply(lambda x: x + ["coexpression_transferred"])

        string = string.drop("coexpression_transferred", axis=1)

        string.loc[string["experiments"] > 0, "source"] = string.loc[
            string["experiments"] > 0, "source"
        ].apply(lambda x: x + ["experiments"])

        string = string.drop("experiments", axis=1)

        string.loc[string["experiments_transferred"] > 0, "source"] = string.loc[
            string["experiments_transferred"] > 0, "source"
        ].apply(lambda x: x + ["experiments_transferred"])

        string = string.drop("experiments_transferred", axis=1)

        string.loc[string["database"] > 0, "source"] = string.loc[
            string["database"] > 0, "source"
        ].apply(lambda x: x + ["database"])

        string = string.drop("database", axis=1)

        string.loc[string["database_transferred"] > 0, "source"] = string.loc[
            string["database_transferred"] > 0, "source"
        ].apply(lambda x: x + ["database_transferred"])

        string = string.drop("database_transferred", axis=1)

        string.loc[string["textmining"] > 0, "source"] = string.loc[
            string["textmining"] > 0, "source"
        ].apply(lambda x: x + ["textmining"])

        string = string.drop("textmining", axis=1)

        string.loc[string["textmining_transferred"] > 0, "source"] = string.loc[
            string["textmining_transferred"] > 0, "source"
        ].apply(lambda x: x + ["textmining_transferred"])

        string = string.drop("textmining_transferred", axis=1)

        string = string.to_dict(orient="list")

        del string_meta

        return string

    def celltalk_to_gene_dict(self, cell_talk, cell_phone):

        cell_talk = pd.DataFrame(cell_talk)

        cell_talk = cell_talk[
            [
                "lr_pair",
                "ligand_gene_symbol",
                "receptor_gene_symbol",
                "ligand_ensembl_protein_id",
                "receptor_ensembl_protein_id",
                "ligand_ensembl_gene_id",
                "receptor_ensembl_gene_id",
                "species",
            ]
        ]

        cell_talk.columns = [
            "lr_pair",
            "protein_1",
            "protein_2",
            "ligand_ensembl_protein_id",
            "receptor_ensembl_protein_id",
            "ligand_ensembl_gene_id",
            "receptor_ensembl_gene_id",
            "species",
        ]

        cell_talk["protein_1"] = [x.upper() for x in cell_talk["protein_1"]]
        cell_talk["protein_2"] = [x.upper() for x in cell_talk["protein_2"]]

        cell_talk["interaction"] = (
            cell_talk["protein_1"] + " -> " + cell_talk["protein_2"]
        )

        cell_talk = cell_talk.reset_index(drop=True)

        cell_phone = pd.DataFrame(cell_phone)
        cell_phone = cell_phone[
            [
                "partner_a",
                "partner_b",
                "protein_name_a",
                "protein_name_b",
                "source",
                "is_ppi",
                "curator",
                "complexPortal_complex",
                "comments",
                "interactors",
                "classification",
                "directionality",
                "modulatory_effect",
            ]
        ]

        cell_phone.columns = [
            "partner_a",
            "partner_b",
            "protein_1",
            "protein_2",
            "source",
            "is_ppi",
            "curator",
            "complexPortal_complex",
            "comments",
            "interactors",
            "classification",
            "directionality",
            "modulatory_effect",
        ]

        cell_phone = cell_phone.reset_index(drop=True)

        for i in cell_phone.index:
            cell_phone.loc[i, "interaction"] = re.sub(
                "-", " -> ", cell_phone.loc[i, "interactors"]
            ).upper()

        full_cell_inc = pd.concat(
            [
                cell_phone[["protein_1", "protein_2", "interaction"]],
                cell_talk[["protein_1", "protein_2", "interaction"]],
            ]
        )
        full_cell_inc = full_cell_inc.drop_duplicates()
        full_cell_inc = full_cell_inc.reset_index(drop=True)

        for i in cell_phone.index:
            cell_phone.at[i, "protein_2"] = re.sub(
                ".* -> ", "", cell_phone.loc[i, "interaction"]
            ).split("+")
            cell_phone.at[i, "protein_1"] = re.sub(
                " -> .*", "", cell_phone.loc[i, "interaction"]
            ).split("+")

        cell_phone["species"] = "Homo sapiens"

        for i in full_cell_inc.index:
            full_cell_inc.at[i, "protein_2"] = re.sub(
                ".* -> ", "", full_cell_inc.loc[i, "interaction"]
            ).split("+")
            full_cell_inc.at[i, "protein_1"] = re.sub(
                " -> .*", "", full_cell_inc.loc[i, "interaction"]
            ).split("+")

        tmp = cell_talk[["interaction", "species"]]
        tmp = tmp.groupby("interaction")[["species"]].agg(list).reset_index()

        full_cell_inc = pd.merge(
            full_cell_inc,
            cell_phone[
                [
                    "directionality",
                    "classification",
                    "modulatory_effect",
                    "interaction",
                    "species",
                ]
            ],
            left_on="interaction",
            right_on="interaction",
            how="left",
        )
        full_cell_inc = pd.merge(
            full_cell_inc,
            tmp,
            left_on="interaction",
            right_on="interaction",
            how="left",
        )

        full_cell_inc = full_cell_inc.reset_index(drop=True)

        full_cell_inc["Species"] = None

        for i in full_cell_inc.index:
            if (
                full_cell_inc.at[i, "species_x"] == full_cell_inc.at[i, "species_x"]
                and full_cell_inc.at[i, "species_y"] == full_cell_inc.at[i, "species_y"]
            ):
                full_cell_inc.at[i, "Species"] = list(
                    set(
                        [full_cell_inc.at[i, "species_x"]]
                        + full_cell_inc.at[i, "species_y"]
                    )
                )
            elif full_cell_inc.at[i, "species_x"] == full_cell_inc.at[i, "species_x"]:
                full_cell_inc.at[i, "Species"] = list(
                    [full_cell_inc.at[i, "species_x"]]
                )
            else:
                full_cell_inc.at[i, "Species"] = list(full_cell_inc.at[i, "species_y"])

        full_cell_inc = full_cell_inc.drop(["species_x", "species_y"], axis=1)

        full_cell_inc["protein_id_1"] = None

        jdci = pd.DataFrame(
            {
                "names": list(
                    set(
                        list(cell_talk["protein_1"].explode())
                        + list(cell_talk["protein_2"].explode())
                        + list(cell_phone["protein_1"].explode())
                        + list(cell_phone["protein_2"].explode())
                    )
                ),
                "id": range(
                    len(
                        list(
                            set(
                                list(cell_talk["protein_1"].explode())
                                + list(cell_talk["protein_2"].explode())
                                + list(cell_phone["protein_1"].explode())
                                + list(cell_phone["protein_2"].explode())
                            )
                        )
                    )
                ),
            }
        )

        jdci["id"] = [int(x) for x in jdci["id"]]

        full_cell_inc["protein_id_2"] = None

        full_cell_inc = full_cell_inc.reset_index(drop=True)

        for i in full_cell_inc.index:
            full_cell_inc.at[i, "protein_id_1"] = list(
                jdci["id"][jdci["names"].isin(full_cell_inc.at[i, "protein_1"])]
            )
            full_cell_inc.at[i, "protein_id_2"] = list(
                jdci["id"][jdci["names"].isin(full_cell_inc.at[i, "protein_2"])]
            )

        gene_dictionary = self.gene_dict

        fetures_id = self.find_fetures_id(gene_dictionary, list(set(jdci["names"])))

        gene_dictionary["id_cell_int"] = None
        gene_dictionary["primary_cell_inc_gene"] = None

        gene_dictionary = pd.DataFrame(gene_dictionary).reset_index(drop=True)

        for inx, gene in enumerate(tqdm(fetures_id["found_genes"])):
            idr = list(
                set(jdci["id"][jdci["names"] == fetures_id["found_genes"][inx]])
            )[0]
            gene_dictionary["id_cell_int"][fetures_id["found_ids"][inx][0]] = idr
            gene_dictionary["primary_cell_inc_gene"][
                fetures_id["found_ids"][inx][0]
            ] = gene

        gene_dictionary = gene_dictionary.to_dict(orient="list")

        full_cell_inc = full_cell_inc.drop(["protein_1", "protein_2"], axis=1)

        self.gene_dict = gene_dictionary

        return (
            cell_talk.to_dict(orient="list"),
            cell_phone.to_dict(orient="list"),
            full_cell_inc.to_dict(orient="list"),
        )

    def update_to_data(self):

        print("\n")
        print("Data update starts...")

        # LOAD MAIN GENE DICTIONARY
        # gene dictionary

        with open(
            os.path.join(self.path_inside, "gene_dictionary_jbio.json"), "r"
        ) as json_file:
            self.gene_dict = json.load(json_file)

        # with open(os.path.join(dw.path_inside, 'gene_dictionary_jbio.json'), 'r') as json_file:
        #     gene_dictionary = (json.load(json_file))

        print("\n Reactome data updating...")

        ##REACTOME LOAD AND ADD TO DICT
        # load reactome
        with open(
            os.path.join(self.path_inside, "reactome_jbio.json"), "r"
        ) as json_file:
            reactome_jbio = json.load(json_file)

        reactome_jbio = self.reactome_to_gene_dict(reactome_jbio)
        reactome_jbio = self.reactome_adjustment(reactome_jbio)

        with open(
            os.path.join(self.path_in_inside, "reactome_jbio_dict.json"), "w"
        ) as json_file:
            json.dump(reactome_jbio, json_file)

        del reactome_jbio

        print("\n Human Protein Atlas data updating...")
        ##HPA LOAD AND ADD TO DICT

        # load HPA
        with open(os.path.join(self.path_inside, "HPA_jbio.json"), "r") as json_file:
            HPA_jbio = json.load(json_file)

        # HPA to dict

        HPA_jbio = self.HPA_to_gene_dict(HPA_jbio)

        HPA_jbio = self.specificity_prepare(HPA_jbio)

        with open(
            os.path.join(self.path_in_inside, "HPA_jbio_dict.json"), "w"
        ) as json_file:
            json.dump(HPA_jbio, json_file)

        del HPA_jbio

        print("\n Disease data updating...")
        ##DISEASES LOAD AND ADD TO DICT

        # load diseases
        with open(
            os.path.join(self.path_inside, "diseases_jbio.json"), "r"
        ) as json_file:
            disease_dict = json.load(json_file)

        # DISEASES

        disease_dict_jbio = self.diseases_to_gene_dict(disease_dict)

        with open(
            os.path.join(self.path_in_inside, "disease_jbio_dict.json"), "w"
        ) as json_file:
            json.dump(disease_dict_jbio, json_file)

        del disease_dict_jbio

        print("\n Viral data updating...")
        ##VIRAL-DISEASES LOAD AND ADD TO DICT
        # VIRAL-DISEASES

        # load viral diseases
        with open(
            os.path.join(self.path_inside, "viral_diseases_jbio.json"), "r"
        ) as json_file:
            viral_dict = json.load(json_file)

        viral_dict_jbio = self.viral_diseases_to_gene_dict(viral_dict)

        with open(
            os.path.join(self.path_in_inside, "viral_jbio_dict.json"), "w"
        ) as json_file:
            json.dump(viral_dict_jbio, json_file)

        del viral_dict_jbio

        print("\n KEGG data updating...")
        ##KEGG LOAD AND ADD TO DICT

        # load kegg
        with open(os.path.join(self.path_inside, "kegg_jbio.json"), "r") as json_file:
            kegg_jbio = json.load(json_file)

        kegg_jbio = self.kegg_to_gene_dict(kegg_jbio)

        with open(
            os.path.join(self.path_in_inside, "kegg_jbio_dict.json"), "w"
        ) as json_file:
            json.dump(kegg_jbio, json_file)

        del kegg_jbio

        print("\n GO-TERM data updating...")
        ##GO-TERM LOAD AND ADD TO DICT
        # load GO-term

        with open(os.path.join(self.path_inside, "goterm_jbio.json"), "r") as json_file:
            go_term_jbio = json.load(json_file)

        go_term_jbio = self.go_to_gene_dict(go_term_jbio)
        go_term_jbio = self.go_adjustment(go_term_jbio)

        with open(
            os.path.join(self.path_in_inside, "goterm_jbio_dict.json"), "w"
        ) as json_file:
            json.dump(go_term_jbio, json_file)

        del go_term_jbio

        ##STRING LOAD AND ADD TO DICT

        print("\n IntAct data updating...")
        # load intact
        with open(os.path.join(self.path_inside, "IntAct_jbio.json"), "r") as json_file:
            IntAct_dict = json.load(json_file)

        IntAct_dict = self.intact_to_gene_dict(IntAct_dict)
        IntAct_dict = self.gene_interactome_prepare_IntAct(IntAct_dict)

        with open(
            os.path.join(self.path_in_inside, "intact_jbio_dict.json"), "w"
        ) as json_file:
            json.dump(IntAct_dict, json_file)

        del IntAct_dict

        print("\n STRING data updating...")
        # load string
        with open(os.path.join(self.path_inside, "string_jbio.json"), "r") as json_file:
            string_dict = json.load(json_file)

        string_dict = self.string_to_gene_dict(string_dict)
        string_dict = self.gene_interactome_prepare_STRING(string_dict)

        with open(
            os.path.join(self.path_in_inside, "string_jbio_dict.json"), "w"
        ) as json_file:
            json.dump(string_dict, json_file)

        del string_dict

        print("\n CellTalk/CellPhone data updating...")
        # load string
        with open(
            os.path.join(self.path_inside, "cell_talk_jbio.json"), "r"
        ) as json_file:
            cell_talk = json.load(json_file)

        with open(
            os.path.join(self.path_inside, "cell_phone_jbio.json"), "r"
        ) as json_file:
            cell_phone = json.load(json_file)

        cell_talk, cell_phone, mutual = self.celltalk_to_gene_dict(
            cell_talk, cell_phone
        )

        with open(
            os.path.join(self.path_in_inside, "cell_talk_jbio.json"), "w"
        ) as json_file:
            json.dump(cell_talk, json_file)

        with open(
            os.path.join(self.path_in_inside, "cell_phone_jbio.json"), "w"
        ) as json_file:
            json.dump(cell_phone, json_file)

        with open(
            os.path.join(self.path_in_inside, "cell_int_jbio.json"), "w"
        ) as json_file:
            json.dump(mutual, json_file)

        gene_dictionary = self.gene_dict
        gene_dictionary = pd.DataFrame(gene_dictionary).reset_index(drop=True)
        gene_dictionary["sid"] = list(gene_dictionary.index)

        with open(
            os.path.join(self.path_in_inside, "gene_dictionary_jbio_annotated.json"),
            "w",
        ) as json_file:
            json.dump(gene_dictionary.to_dict(orient="list"), json_file)

        del cell_talk, cell_phone, mutual, gene_dictionary

        print("\n")
        print("Process has finished...")

    def serialize_data(self, value):
        if isinstance(value, (list)):
            return json.dumps(value)
        return value

    def create_SQL(self):

        print("\nDatabase creation...")

        conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

        print("\nAdding REACTOME to DB...")

        reactome = pd.DataFrame(self.get_REACTOME())

        reactome = reactome.applymap(self.serialize_data)

        reactome.to_sql("REACTOME", conn, if_exists="replace", index=False)

        del reactome

        print("\nAdding RefGenome to DB...")

        ref_gen = pd.DataFrame(self.get_REF_GEN())

        occ_dict = {}

        occ_dict["HPA"] = len(ref_gen["id_HPA"][ref_gen["id_HPA"].notna()])
        occ_dict["REACTOME"] = len(
            ref_gen["id_reactome"][ref_gen["id_reactome"].notna()]
        )
        occ_dict["GO-TERM"] = len(ref_gen["id_GO"][ref_gen["id_GO"].notna()])
        occ_dict["ViMIC"] = len(
            ref_gen["id_viral_diseases"][ref_gen["id_viral_diseases"].notna()]
        )
        occ_dict["DISEASES"] = len(
            ref_gen["id_diseases"][ref_gen["id_diseases"].notna()]
        )
        occ_dict["IntAct"] = len(ref_gen["id_IntAct"][ref_gen["id_IntAct"].notna()])
        occ_dict["CellConnections"] = len(
            ref_gen["id_cell_int"][ref_gen["id_cell_int"].notna()]
        )
        occ_dict["DISEASES"] = len(
            ref_gen["id_diseases"][ref_gen["id_diseases"].notna()]
        )
        occ_dict["Genes_Mus_musculus"] = len(
            ref_gen["gene_Mus_musculus"][ref_gen["gene_Mus_musculus"].notna()]
        )
        occ_dict["Genes_Homo_sapiens"] = len(
            ref_gen["gene_Homo_sapiens"][ref_gen["gene_Homo_sapiens"].notna()]
        )
        occ_dict["Genes_Rattus_norvegicus"] = len(
            ref_gen["gene_Rattus_norvegicus"][ref_gen["gene_Rattus_norvegicus"].notna()]
        )

        with open(os.path.join(self.path_in_inside, "occ_dict.json"), "w") as json_file:
            json.dump(occ_dict, json_file)

        ref_gen = ref_gen.applymap(self.serialize_data)

        ref_gen.to_sql("RefGenome", conn, if_exists="replace", index=False)

        occ_dict["RefGenome"] = int(len(set(ref_gen["sid"])))

        del ref_gen

        print("\nAdding HPA to DB...")

        HPA = self.get_HPA()

        for i in HPA.keys():

            tmp_HPA = pd.DataFrame(HPA[i])

            tmp_HPA = tmp_HPA.applymap(self.serialize_data)

            tmp_HPA.to_sql("HPA_" + i, conn, if_exists="replace", index=False)

        del HPA, tmp_HPA

        print("\nAdding Diseases to DB...")

        disease = pd.DataFrame(self.get_DISEASES())

        disease = disease.applymap(self.serialize_data)

        disease.to_sql("disease", conn, if_exists="replace", index=False)

        del disease

        print("\nAdding ViMIC to DB...")

        vimic = pd.DataFrame(self.get_ViMIC())

        vimic = vimic.applymap(self.serialize_data)

        vimic.to_sql("ViMIC", conn, if_exists="replace", index=False)

        del vimic

        print("\nAdding KEGG to DB...")

        kegg = pd.DataFrame(self.get_KEGG())

        kegg = kegg.applymap(self.serialize_data)

        kegg.to_sql("KEGG", conn, if_exists="replace", index=False)

        del kegg

        print("\nAdding GO-TERM to DB...")

        go = self.get_GO()

        for i in go.keys():

            tmp_GO = pd.DataFrame(go[i])

            tmp_GO = tmp_GO.applymap(self.serialize_data)

            tmp_GO.to_sql("GO_" + i, conn, if_exists="replace", index=False)

        del go, tmp_GO

        print("\nAdding IntAct to DB...")

        intact = self.get_IntAct()

        for i in intact.keys():

            tmp_IntAct = pd.DataFrame(intact[i])

            tmp_IntAct = tmp_IntAct.applymap(self.serialize_data)

            tmp_IntAct.to_sql("IntAct_" + i, conn, if_exists="replace", index=False)

        del intact, tmp_IntAct

        print("\nAdding STRING to DB...")

        string = pd.DataFrame(self.get_STRING())

        string = string.applymap(self.serialize_data)

        string.to_sql("STRING", conn, if_exists="replace", index=False)

        del string

        print("\nAdding CellTalk/CellPhone to DB...")

        interactions = pd.DataFrame(self.get_interactions())

        interactions = interactions.explode("Species")
        interactions = interactions.explode("protein_id_1")
        interactions = interactions.explode("protein_id_2")

        interactions = interactions.reset_index(drop=True)

        interactions = interactions.applymap(self.serialize_data)

        interactions.to_sql("CellInteractions", conn, if_exists="replace", index=False)

        del interactions

        conn.close()

    def ZIP(self):
        with zipfile.ZipFile(
            os.path.join(os.path.dirname(self.path_inside), "data.zip"),
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as zipf:
            for folder, _, files in os.walk(self.path_inside):
                for file in files:
                    file_path = os.path.join(folder, file)
                    relative_path = os.path.relpath(file_path, self.path_inside)
                    zipf.write(file_path, arcname=relative_path)

    def get_ZIP(self, path=os.getcwd()):

        source_path = os.path.join(os.path.dirname(self.path_inside), "data.zip")

        destination_path = os.path.join(path, "data.zip")

        shutil.move(source_path, destination_path)


class UpdatePanel(Donwload, DataAdjustment):

    def update_from_sources(self, **kwargs):
        """
        This function checks all source databases and updates the GEDSpy database without supervision from the library author's side.


        Returns:
            Updated GEDSpy base.
        """

        try:
            import time

            print("\n")
            print(
                "!!!WARNING!!! You have used the update_from_sources() option, the data in the GEDSpy library will be overwritten. We cannot guarantee that the authors of individual databases have not made changes that were not foreseen in GEDSpy and may cause unforeseen changes. If you want to restore the previous version of the data, reinstall the library. Data in the library will be updated and checked by the author in subsequent versions of the library. However, if you want access to the latest data, you can use it."
            )
            time.sleep(20)

            print("\nPrevious data removeing!")

            files_to_delete = [
                "cell_phone_jbio.json",
                "cell_talk_jbio.json",
                "diseases_jbio.json",
                "gene_dictionary_jbio.json",
                "goterm_jbio.json",
                "HPA_jbio.json",
                "IntAct_jbio.json",
                "kegg_jbio.json",
                "reactome_jbio.json",
                "string_jbio.json",
                "update.dat",
                "viral_diseases_jbio.json",
            ]

            for file_name in files_to_delete:
                file_path = os.path.join(self.path_inside, file_name)
                if os.path.exists(file_path):  # Check if file exists
                    try:
                        os.remove(file_path)
                        print(f"The file {file_name} was removed successfully")
                    except OSError as e:
                        print(f"Error deleting the file {file_name}: {e}")
                else:
                    print(f"The file {file_name} does not exist, skipping...")

            files = [
                f
                for f in os.listdir(self.path_in_inside)
                if os.path.isfile(os.path.join(self.path_in_inside, f))
            ]

            for f in files:
                if os.path.exists(os.path.join(self.path_in_inside, f)):

                    os.remove(os.path.join(self.path_in_inside, f))

                    print("The file was removed successfully")

                else:
                    print(f"Error deleting the file: {f}")

            if "admin_user" in kwargs:
                self.update_downloading(password=kwargs["admin_user"])
            else:
                self.update_downloading(password=None)

            self.update_to_data()

            self.create_SQL()

            if "admin_user" in kwargs:
                self.ZIP()

        except:
            print("\n")
            print("Something went wrong!")

    def get_latest_version(self, package_name):
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        data = response.json()
        return data["info"]["version"]

    def get_installed_version(self, package_name):
        try:
            version = pkg_resources.get_distribution(package_name).version
            return version
        except pkg_resources.DistributionNotFound:
            return "Not installed"

    def update_library_database(
        self,
        force=False,
        URL="https://drive.google.com/uc?id=1LQXI7zEXyvywjBz2TX1QBXN60Abia6WP",
        first=False,
    ):
        """
        This method checks if the newest version of GEDS data is available for the GEDSpy library and updates it.

        Args:
            force (bool) - if True user force update of GEDS data independent of the GEDSpy version
            URL (str) - provide URL of the database you wish to use. Default: URL for the newest db version

        Returns:
            Updated by the author the newest version of GEDS data base.
        """

        if force:

            print("\nGEDSpy data update was forced by the user")
            print("\nUpdate has started...")
            gdown.download(
                URL, os.path.join(os.path.dirname(self.path_inside), "data.zip")
            )
            shutil.rmtree(self.path_inside, ignore_errors=True)
            os.makedirs(self.path_inside, exist_ok=True)
            with zipfile.ZipFile(
                os.path.join(os.path.dirname(self.path_inside), "data.zip"), "r"
            ) as zipf:
                zipf.extractall(self.path_inside)
            os.remove(os.path.join(os.path.dirname(self.path_inside), "data.zip"))

            print("\n")
            print(
                'Update completed, if you want to check if the data version has changed, use "check_last_update()"'
            )

            if first is False:

                print(
                    "In addition, we recommend upgrading the GEDSpy version via pip by typing pip install GEDSpy --upgrade."
                )

        elif self.get_latest_version("GEDSpy") == self.get_installed_version("GEDSpy"):
            print("\n")
            print(
                "GEDSpy is up to date for its version. If you want to download the newest data from the original sources, you can use the update_from_sources() method."
            )

        elif self.get_latest_version("GEDSpy") != self.get_installed_version("GEDSpy"):

            print("\nUpdate has started...")
            gdown.download(
                URL, os.path.join(os.path.dirname(self.path_inside), "data.zip")
            )
            shutil.rmtree(self.path_inside, ignore_errors=True)
            os.makedirs(self.path_inside, exist_ok=True)
            with zipfile.ZipFile(
                os.path.join(os.path.dirname(self.path_inside), "data.zip"), "r"
            ) as zipf:
                zipf.extractall(self.path_inside)
            os.remove(os.path.join(os.path.dirname(self.path_inside), "data.zip"))

            print("\n")
            print(
                'Update completed, if you want to check if the data version has changed, use "check_last_update()"'
            )
            print(
                "In addition, we recommend upgrading the GEDSpy version via pip by typing pip install GEDSpy --upgrade."
            )
