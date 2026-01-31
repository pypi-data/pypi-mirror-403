# Requirements import
import json
import os
import re
import sqlite3
import warnings
from collections import Counter

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import pkg_resources
import seaborn as sns
from matplotlib import rc
from matplotlib.gridspec import GridSpec
from scipy.cluster.hierarchy import dendrogram, leaves_list, linkage
from scipy.stats import binomtest, fisher_exact
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm

rc("svg", fonttype="path")


pd.options.mode.chained_assignment = None
warnings.filterwarnings("ignore")


# Geta data directory


class PathMetadata:
    def __init__(self):

        def get_package_directory():
            return pkg_resources.resource_filename(__name__, "")

        self._cwd = get_package_directory()
        self.path_inside = os.path.join(self._cwd, "data")
        self.path_in_inside = os.path.join(self._cwd, "data", "in_use")
        self.path_tmp = os.path.join(self._cwd, "data", "tmp")

        os.makedirs(self.path_inside, exist_ok=True)
        os.makedirs(self.path_in_inside, exist_ok=True)
        os.makedirs(self.path_tmp, exist_ok=True)

    def __repr__(self):
        return (
            f"PathMetadata(\n"
            f"  path_inside='{self.path_inside}',\n"
            f"  path_in_inside='{self.path_in_inside}',\n"
            f"  path_tmp='{self.path_tmp}'\n"
            f")"
        )


class GetDataRaw(PathMetadata):

    def __init__(self):
        super().__init__()

    def get_raw_REACTOME(self):
        """
        This method gets the REACTOME data downloaded from source.

        Source: https://reactome.org/

        Returns:
           dict: REACTOME data
        """

        try:
            with open(
                os.path.join(self.path_inside, "reactome_jbio.json"), "r"
            ) as json_file:
                reactome_jbio = json.load(json_file)

            return reactome_jbio

        except:
            print("Something went wrong. Check the function input data and try again!")

    def get_raw_REF_GEN(self):
        """
        This method gets the REF_GEN which is the combination of Homo sapiens / Mus musculus / Rattus norvegicus genomes for scientific use.

        Source: NCBI [https://www.ncbi.nlm.nih.gov/]

        Returns:
           dict: Combination of Homo sapiens / Mus musculus / Rattus norvegicus genomes
        """

        try:

            with open(
                os.path.join(self.path_inside, "gene_dictionary_jbio.json"), "r"
            ) as json_file:
                gene_dictionary = json.load(json_file)

            return gene_dictionary

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_raw_REF_GEN_RNA_SEQ(self):
        """
        This method gets the tissue-specific RNA-SEQ data including:
            -human_tissue_expression_HPA
            -human_tissue_expression_RNA_total_tissue
            -human_tissue_expression_fetal_development_circular

        Source: NCBI [https://www.ncbi.nlm.nih.gov/]


        Returns:
           dict: Tissue specific RNA-SEQ data
        """

        try:

            with open(
                os.path.join(self.path_in_inside, "tissue_expression_HPA.json"), "r"
            ) as json_file:
                human_tissue_expression_HPA = json.load(json_file)

            with open(
                os.path.join(
                    self.path_in_inside, "tissue_expression_RNA_total_tissue.json"
                ),
                "r",
            ) as json_file:
                human_tissue_expression_RNA_total_tissue = json.load(json_file)

            with open(
                os.path.join(
                    self.path_in_inside,
                    "tissue_expression_fetal_development_circular.json",
                ),
                "r",
            ) as json_file:
                human_tissue_expression_fetal_development_circular = json.load(
                    json_file
                )

            rna_seq_list = {
                "tissue_expression_HPA": human_tissue_expression_HPA,
                "tissue_expression_RNA_total_tissue": human_tissue_expression_RNA_total_tissue,
                "tissue_expression_fetal_development_circular": human_tissue_expression_fetal_development_circular,
            }

            return rna_seq_list

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_raw_HPA(self):
        """
        This method gets the HPA (Human Protein Atlas) data.

        Source: https://www.proteinatlas.org/


        Returns:
           dict: HPA data
        """

        try:

            with open(
                os.path.join(self.path_inside, "HPA_jbio.json"), "r"
            ) as json_file:
                HPA_jbio = json.load(json_file)

            return HPA_jbio

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_raw_DISEASES(self):
        """
        This method gets the Human Diseases data.

        Source: https://diseases.jensenlab.org/Search


        Returns:
           dict: DISEASES data
        """

        try:

            # load diseases
            with open(
                os.path.join(self.path_inside, "diseases_jbio.json"), "r"
            ) as json_file:
                disease_dict_jbio = json.load(json_file)

            return disease_dict_jbio

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_raw_ViMIC(self):
        """
        This method gets the ViMIC data.

        Source: http://bmtongji.cn/ViMIC/index.php


        Returns:
           dict: ViMIC data
        """

        try:

            # load viral diseases
            with open(
                os.path.join(self.path_inside, "viral_diseases_jbio.json"), "r"
            ) as json_file:
                viral_dict_jbio = json.load(json_file)

            return viral_dict_jbio

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_raw_KEGG(self):
        """
        This method gets the KEGG data.

        Source: https://www.genome.jp/kegg/


        Returns:
           dict: KEGG data
        """

        try:

            # load kegg
            with open(
                os.path.join(self.path_inside, "kegg_jbio.json"), "r"
            ) as json_file:
                kegg_jbio = json.load(json_file)

            return kegg_jbio

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_raw_GO(self):
        """
        This method gets the GO-TERM data.

        Source: https://geneontology.org/


        Returns:
           dict: GO-TERM data
        """

        try:

            with open(
                os.path.join(self.path_inside, "goterm_jbio.json"), "r"
            ) as json_file:
                go_term_jbio = json.load(json_file)

            return go_term_jbio

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_raw_IntAct(self):
        """
        This method gets the IntAct data.

        Source: https://www.ebi.ac.uk/intact/home


        Returns:
           dict: IntAct data
        """

        try:
            with open(
                os.path.join(self.path_inside, "IntAct_jbio.json"), "r"
            ) as json_file:
                IntAct_dict = json.load(json_file)

            return IntAct_dict

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_raw_STRING(self):
        """
        This method gets the STRING data.

        Source: https://string-db.org/


        Returns:
           dict: STRING data
        """

        try:
            with open(
                os.path.join(self.path_inside, "string_jbio.json"), "r"
            ) as json_file:
                string_dict = json.load(json_file)

            return string_dict

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_raw_CellTalk(self):
        """
        This method gets the CellTalk data.

        Source: https://tcm.zju.edu.cn/celltalkdb/


        Returns:
           dict: CellTalk data
        """

        try:
            with open(
                os.path.join(self.path_inside, "cell_talk_jbio.json"), "r"
            ) as json_file:
                cell_talk = json.load(json_file)

            return cell_talk

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_raw_CellPhone(self):
        """
        This method gets the CellPhone data.

        Source: https://www.cellphonedb.org/


        Returns:
           dict: CellPhone data
        """

        try:
            with open(
                os.path.join(self.path_inside, "cell_phone_jbio.json"), "r"
            ) as json_file:
                cell_phone = json.load(json_file)

            return cell_phone

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")


class GetData(PathMetadata):

    def __init__(self):
        super().__init__()

    def get_REACTOME(self):
        """
        This method gets the REACTOME data including the id to connect with REF_GENE by id_reactome

        Returns:
           dict: REACTOME data
        """

        try:
            with open(
                os.path.join(self.path_in_inside, "reactome_jbio_dict.json"), "r"
            ) as json_file:
                reactome_jbio = json.load(json_file)

            return reactome_jbio

        except:
            print("Something went wrong. Check the function input data and try again!")

    def get_REF_GEN(self):
        """
        This method gets the REF_GEN which is the combination of Homo sapiens / Mus musculus / Rattus norvegicus genomes for scientific use.

        Returns:
           dict: Combination of Homo sapiens / Mus musculus / Rattus norvegicus genomes
        """

        try:

            with open(
                os.path.join(
                    self.path_in_inside, "gene_dictionary_jbio_annotated.json"
                ),
                "r",
            ) as json_file:
                gene_dictionary = json.load(json_file)

            return gene_dictionary

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_REF_GEN_RNA_SEQ(self):
        """
        This method gets the tissue-specific RNA-SEQ data including:
            -human_tissue_expression_HPA
            -human_tissue_expression_RNA_total_tissue
            -human_tissue_expression_fetal_development_circular


        Returns:
           dict: Tissue specific RNA-SEQ data
        """

        try:

            with open(
                os.path.join(self.path_in_inside, "tissue_expression_HPA.json"), "r"
            ) as json_file:
                human_tissue_expression_HPA = json.load(json_file)

            with open(
                os.path.join(
                    self.path_in_inside, "tissue_expression_RNA_total_tissue.json"
                ),
                "r",
            ) as json_file:
                human_tissue_expression_RNA_total_tissue = json.load(json_file)

            with open(
                os.path.join(
                    self.path_in_inside,
                    "tissue_expression_fetal_development_circular.json",
                ),
                "r",
            ) as json_file:
                human_tissue_expression_fetal_development_circular = json.load(
                    json_file
                )

            rna_seq_list = {
                "tissue_expression_HPA": human_tissue_expression_HPA,
                "tissue_expression_RNA_total_tissue": human_tissue_expression_RNA_total_tissue,
                "tissue_expression_fetal_development_circular": human_tissue_expression_fetal_development_circular,
            }

            return rna_seq_list

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_HPA(self):
        """
        This method gets the HPA (Human Protein Atlas) data including the id to connect with REF_GENE by id_HPA

        Returns:
           dict: HPA data
        """

        try:

            with open(
                os.path.join(self.path_in_inside, "HPA_jbio_dict.json"), "r"
            ) as json_file:
                HPA_jbio = json.load(json_file)

            return HPA_jbio

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_DISEASES(self):
        """
        This method gets the DISEASES data including the id to connect with REF_GENE by id_diseases

        Returns:
           dict: DISEASES data
        """

        try:

            # load diseases
            with open(
                os.path.join(self.path_in_inside, "disease_jbio_dict.json"), "r"
            ) as json_file:
                disease_dict_jbio = json.load(json_file)

            return disease_dict_jbio

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_ViMIC(self):
        """
        This method gets the ViMIC data including the id to connect with REF_GENE by id_viral_diseases

        Returns:
           dict: ViMIC data
        """

        try:

            # load viral diseases
            with open(
                os.path.join(self.path_in_inside, "viral_jbio_dict.json"), "r"
            ) as json_file:
                viral_dict_jbio = json.load(json_file)

            return viral_dict_jbio

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_KEGG(self):
        """
        This method gets the KEGG data including the id to connect with REF_GENE by id_KEGG

        Returns:
           dict: KEGG data
        """

        try:

            # load kegg
            with open(
                os.path.join(self.path_in_inside, "kegg_jbio_dict.json"), "r"
            ) as json_file:
                kegg_jbio = json.load(json_file)

            return kegg_jbio

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_GO(self):
        """
        This method gets the GO-TERM data including the id to connect with REF_GENE by id_GO

        Returns:
           dict: GO-TERM data
        """

        try:

            with open(
                os.path.join(self.path_in_inside, "goterm_jbio_dict.json"), "r"
            ) as json_file:
                go_term_jbio = json.load(json_file)

            return go_term_jbio

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_IntAct(self):
        """
        This method gets the IntAct data including the id to connect with REF_GENE by id_IntAct

        Returns:
           dict: IntAct data
        """

        try:
            with open(
                os.path.join(self.path_in_inside, "intact_jbio_dict.json"), "r"
            ) as json_file:
                IntAct_dict = json.load(json_file)

            return IntAct_dict

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_STRING(self):
        """
        This method gets the STRING data including the id to connect with REF_GENE by id_string

        Returns:
           dict: STRING data
        """

        try:
            with open(
                os.path.join(self.path_in_inside, "string_jbio_dict.json"), "r"
            ) as json_file:
                string_dict = json.load(json_file)

            return string_dict

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_CellTalk(self):
        """
        This method gets the CellTalk data after adjustment.

        Returns:
           dict: CellTalk data
        """

        try:
            with open(
                os.path.join(self.path_in_inside, "cell_talk_jbio.json"), "r"
            ) as json_file:
                cell_talk = json.load(json_file)

            return cell_talk

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_CellPhone(self):
        """
        This method gets the CellPhone data after adjustment.

        Returns:
           dict: CellPhone data
        """

        try:
            with open(
                os.path.join(self.path_in_inside, "cell_phone_jbio.json"), "r"
            ) as json_file:
                cell_phone = json.load(json_file)

            return cell_phone

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")

    def get_interactions(self):
        """
        This method gets the CellPhone & CellTalk data including the id to connect with REF_GENE by id_interactions.

        Returns:
           dict: CellInteractions data
        """

        try:
            with open(
                os.path.join(self.path_in_inside, "cell_int_jbio.json"), "r"
            ) as json_file:
                cell_int = json.load(json_file)

            return cell_int

        except:
            print("\n")
            print("Something went wrong. Check the function input data and try again!")


class Enrichment(GetData):
    """
    The `Enrichment` class provides tools to analyze and extract essential information about gene sets, including their functions and interactions, using resources such as KEGG, REACTOME, GO-TERM, Human Protein Atlas (HPA), NCBI, and protein interaction databases like IntAct and STRING.

    This class supports cross-species analysis, enabling translation studies between mouse, rat, and human.

    Users can specify the species context for gene/protein name searching and select the data sources to be used for enrichment analysis. Supported species include:
        - 'Mus musculus' (mouse)
        - 'Homo sapiens' (human)
        - 'Rattus norvegicus' (rat)

    """

    def __init__(self):
        self.features_list = None
        self.genome = None
        self.found_genes = None
        self.species_study = ["Mus musculus", "Homo sapiens", "Rattus norvegicus"]
        self.species_ids = None
        self.species_genes = ["Mus musculus", "Homo sapiens", "Rattus norvegicus"]
        self.ids = None
        self.HPA = None
        self.STRING = None
        self.GO_TERM = None
        self.REACTOME = None
        self.CellCon = None
        self.IntAct = None
        self.ViMIC = None
        self.Diseases = None
        self.KEGG = None
        self.mapper = None
        self.RNA_SEQ = None

        super().__init__()

    def reduce_extended_gtf(self, names):
        return list(
            set(
                [
                    re.sub(
                        r"\.str.*",
                        "",
                        re.sub(r"\.chr.*", "", re.sub(r"\.var.*", "", n)),
                    )
                    for n in names
                ]
            )
        )

    def set_gene_species(self, species: list):
        """
        Sets the `self.species_genes` parameter, allowing the user to specify the species for gene/protein scharching on names.

        Supported species options are:
            - 'Mus musculus'
            - 'Homo sapiens'
            - 'Rattus norvegicus'

        Args:
            species (list) - list of species

        Default: ['Mus musculus', 'Homo sapiens', 'Rattus norvegicus']

        """

        values = ["Mus musculus", "Homo sapiens", "Rattus norvegicus"]

        if all(value in values for value in species):
            self.species_genes = species

        else:

            raise ValueError(
                "\nValues in list should be included in STRING, Affinomics, Alzheimers, BioCreative, Cancer, Cardiac, Chromatin, Coronavirus, Diabetes, Huntington`s, IBD, Neurodegeneration, Parkinsons"
            )

    def set_data_species(self, species: list):
        """
        Sets the `self.species_study` parameter, allowing the user to specify the species context for gene/protein information used in gene set enrichment analysis.

        Supported species options are:
            - 'Mus musculus'
            - 'Homo sapiens'
            - 'Rattus norvegicus'

        Args:
            species (list) - list of species

        Default: ['Mus musculus', 'Homo sapiens', 'Rattus norvegicus']

        """

        values = ["Mus musculus", "Homo sapiens", "Rattus norvegicus"]

        if all(value in values for value in species):
            self.species_study = species

        else:

            raise ValueError(
                "\nValues in list should be included in STRING, Affinomics, Alzheimers, BioCreative, Cancer, Cardiac, Chromatin, Coronavirus, Diabetes, Huntington`s, IBD, Neurodegeneration, Parkinsons"
            )

    def show_founded_features(self):
        return self.found_genes["found_genes"]

    def show_non_founded_features(self):
        return self.found_genes["not_found"]

    def get_gene_info(self):

        if isinstance(self.genome, pd.DataFrame):

            return self.genome.to_dict(orient="list")

        else:
            raise ValueError("\nLack of Genome data...")

    def get_RNA_SEQ(self):
        """
        This method returns the RNAseq information.
        It includes specificity to the following data sets:
            -human_tissue_expression_HPA
            -human_tissue_expression_RNA_total_tissue
            -human_tissue_expression_fetal_development_circular

        Returns:
            Returns `self.RNA_SEQ` with RNAseq information enriched using the `self.enriche_RNA_SEQ` method.
        """

        if self.RNA_SEQ != None:

            return self.RNA_SEQ

        else:
            raise ValueError("\nLack of enrichment of RNA-SEQ data...")

    def get_HPA(self):
        """
        This method returns the Human Protein Atlas (HPA) information.
        It includes specificity to the following categories:
            - HPA_RNA_tissue
            - HPA_RNA_single_cell
            - HPA_RNA_cancer
            - HPA_RNA_brain
            - HPA_RNA_blood
            - HPA_RNA_blood_lineage
            - HPA_RNA_cell_line
            - HPA_RNA_mouse_brain_region
            - HPA_subcellular_location
            - HPA_blood_markers

        Returns:
            Returns `self.HPA` with Human Protein Atlas information enriched using the `self.enriche_specificiti` method.
        """

        if self.HPA != None:

            return self.HPA

        else:
            raise ValueError("\nLack of enrichment of HPA data...")

    def get_STRING(self):
        """
        This method returns the STRING information.

        Returns:
            Returns `self.STRING` with STRING information enriched using the `self.enriche_STRING` method.
        """

        if self.STRING != None:

            return self.STRING

        else:
            raise ValueError("\nLack of enrichment of STRING data...")

    def get_GO_TERM(self):
        """
        This method returns the GeneOntology (GO-TERM) information.

        Returns:
            Returns `self.GO` with GeneOntology (GO-TERM) information enriched using the `self.enriche_GOTERM` method.
        """

        if self.GO_TERM != None:

            return self.GO_TERM

        else:
            raise ValueError("\nLack of enrichment of GO-TERM data...")

    def get_REACTOME(self):
        """
        This method returns the Reactome information.

        Returns:
            Returns `self.REACTOME` with Reactome information enriched using the `self.enriche_REACTOME` method.
        """

        if self.REACTOME != None:

            return self.REACTOME

        else:
            raise ValueError("\nLack of enrichment of REACTOME data...")

    def get_CellCon(self):
        """
        This method returns the CellPhone / CellTalk information.

        Returns:
            Returns `self.CellCon` with Human Protein Atlas information enriched using the `self.enriche_CellCon` method.
        """

        if self.CellCon != None:

            return self.CellCon

        else:
            raise ValueError("\nLack of enrichment of CellCon data...")

    def get_IntAct(self):
        """
        This method returns the IntAct information.
        It includes specificity to the following data sets:
            - Affinomics
            - Alzheimers
            - BioCreative
            - Cancer
            - Cardiac
            - Chromatin
            - Coronavirus
            - Cyanobacteria
            - Diabetes
            - Huntington
            - IBD
            - Neurodegeneration
            - Parkinsons
            - Rare Diseases
            - Ulcerative

        Returns:
            Returns `self.IntAct` with IntAct information enriched using the `self.enriche_IntAct` method.
        """

        if self.IntAct != None:

            return self.IntAct

        else:
            raise ValueError("\nLack of enrichment of IntAct data...")

    def get_KEGG(self):
        """
        This method returns the Kyoto Encyclopedia of Genes and Genomes (KEGG) information.

        Returns:
            Returns `self.KEGG` with KEGG information enriched using the `self.enriche_KEGG` method.
        """

        if self.KEGG != None:

            return self.KEGG

        else:
            raise ValueError("\nLack of enrichment of KEGG data...")

    def get_DISEASES(self):
        """
        This method returns the Human Diseases information.

        Returns:
            Returns `self.Diseases` with Human Diseases information enriched using the `self.enriche_DISEASES` method.
        """

        if self.Diseases != None:

            return self.Diseases

        else:
            raise ValueError("\nLack of enrichment of Diseases data...")

    def get_ViMIC(self):
        """
        This method returns the Viral Diseases (ViMIC) information.

        Returns:
            Returns `self.ViMIC` with Viral Diseases (ViMIC) information enriched using the `self.enriche_ViMIC` method.
        """

        if self.ViMIC != None:

            return self.ViMIC

        else:
            raise ValueError("\nLack of enrichment of ViMIC data...")

    def get_columns_names(self):
        conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        conn.close()

        for table in tables:
            print(table[0])

    def get_results(self):
        """
        This method returns the full enrichment analysis dictionary containing on keys:
            - 'gene_info' - genome information for the selected gene set [see `self.get_gene_info`]
            - 'HPA' - Human Protein Atlas (HPA) [see 'self.get_HPA']
            - 'KEGG' - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see 'self.get_KEGG']
            - 'GO-TERM' - GeneOntology (GO-TERM) [see 'self.get_GO_TERM']
            - 'REACTOME' - Reactome [see 'self.get_REACTOME']
            - 'DISEASES' - Human Diseases [see 'self.get_DISEASES']
            - 'ViMIC' - Viral Diseases (ViMIC) [see 'self.get_ViMIC']
            - 'IntAct' - IntAct [see 'self.get_IntAct']
            - 'STRING' - STRING [see 'self.get_STRING']
            - 'CellConnections' - CellConnections (CellPhone / CellTalk) [see 'self.get_CellCon']
            - 'RNA-SEQ' - RNAseq data specific to tissues [see 'self.get_RNA_SEQ']

        Returns:
            dict (dict) - full enrichment data
        """

        results = {}

        try:
            results["gene_info"] = self.get_gene_info()
        except:
            pass

        try:
            results["HPA"] = self.get_HPA()
        except:
            pass

        try:
            results["STRING"] = self.get_STRING()
        except:
            pass

        try:
            results["GO-TERM"] = self.get_GO_TERM()
        except:
            pass

        try:
            results["REACTOME"] = self.get_REACTOME()
        except:
            pass

        try:
            results["CellConnections"] = self.get_CellCon()
        except:
            pass

        try:
            results["IntAct"] = self.get_IntAct()
        except:
            pass

        try:
            results["KEGG"] = self.get_KEGG()
        except:
            pass

        try:
            results["DISEASES"] = self.get_DISEASES()
        except:
            pass

        try:
            results["ViMIC"] = self.get_ViMIC()
        except:
            pass

        try:
            results["RNA-SEQ"] = self.get_RNA_SEQ()
        except:
            pass

        results["species"] = {}
        results["species"]["species_genes"] = self.species_genes
        results["species"]["species_study"] = self.species_study

        return results

    def deserialize_data(self, value):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def load_genome(self):

        print("\n")
        print("Metadata loading...")

        conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

        query = "SELECT * FROM RefGenome;"

        df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

        conn.close()

        self.genome = df

    def spec_dic(self):

        species = self.species_genes

        if (
            isinstance(species, list)
            and len(species) == 1
            and "Homo sapiens" in species
        ):
            tf_h = ["Homo sapiens" in x for x in self.genome["species"]]
        elif (
            isinstance(species, list)
            and len(species) == 1
            and "Mus musculus" in species
        ):
            tf_h = ["Mus musculus" in x for x in self.genome["species"]]
        elif (
            isinstance(species, list)
            and len(species) == 1
            and "Rattus norvegicus" in species
        ):
            tf_h = ["Rattus norvegicus" in x for x in self.genome["species"]]
        elif (
            isinstance(species, list)
            and len(species) == 2
            and "Homo sapiens" in species
            and "Mus musculus" in species
        ):
            tf_h = [
                "Homo sapiens" in x or "Mus musculus" in x
                for x in self.genome["species"]
            ]
        elif (
            isinstance(species, list)
            and len(species) == 2
            and "Homo sapiens" in species
            and "Rattus norvegicus" in species
        ):
            tf_h = [
                "Homo sapiens" in x or "Rattus norvegicus" in x
                for x in self.genome["species"]
            ]
        elif (
            isinstance(species, list)
            and len(species) == 2
            and "Mus musculus" in species
            and "Rattus norvegicus" in species
        ):
            tf_h = [
                "Rattus norvegicus" in x or "Mus musculus" in x
                for x in self.genome["species"]
            ]
        elif (
            isinstance(species, list)
            and len(species) == 3
            and "Mus musculus" in species
            and "Rattus norvegicus" in species
            and "Homo sapiens" in species
        ):
            tf_h = [True for x in self.genome["species"]]  # Selects all species
        else:
            raise ValueError("Invalid species specified.")

        ids = [value for value, flag in zip(self.genome["sid"], tf_h) if flag]

        self.species_ids = ids

    def find_fetures_id(self):

        genome_dict = pd.DataFrame(self.genome)
        genome_dict = genome_dict.reset_index(drop=True)
        gene = []
        not_found = []
        ids = []
        for fet in tqdm(self.features_list):
            idg = genome_dict["sid"][
                genome_dict["possible_names"].apply(lambda x: fet.upper() in x)
            ]
            if len(idg) > 0:
                ids.append(int(idg))
                gene.append(fet)
            else:
                not_found.append(fet)

        self.found_genes = {
            "found_genes": gene,
            "found_ids": ids,
            "not_found": not_found,
        }

    def v1_is_in_v2(self):
        v1 = self.found_genes["found_ids"]
        v2 = self.species_ids
        v3 = [x for x in v1 if x in v2]
        self.ids = v3

    def return_dictionary(self):
        genome_dict = pd.DataFrame(self.genome)
        genome_dict = genome_dict[genome_dict["sid"].isin(self.ids)]
        genome_dict = genome_dict.reset_index(drop=True)

        self.genome = genome_dict

    def add_found_names(self):

        mapper = dict(
            zip(self.found_genes["found_ids"], self.found_genes["found_genes"])
        )
        gene_dictionary = pd.DataFrame(self.genome)
        gene_dictionary["found_names"] = gene_dictionary["sid"]
        gene_dictionary["found_names"] = gene_dictionary["found_names"].map(mapper)

        self.genome = gene_dictionary

    def enriche_RNA_SEQ(self):
        """
        This method selects elements from the GEDS database that are included in the RNAseq information.
        It includes specificity to the following data sets:
            -human_tissue_expression_HPA
            -human_tissue_expression_RNA_total_tissue
            -human_tissue_expression_fetal_development_circular

        Returns:
            Updates `self.RNA_SEQ` with RNAseq information.
            To retrieve the results, use the `self.get_RNA_SEQ` method.
        """

        if (
            isinstance(self.genome, pd.DataFrame)
            and "found_names" in self.genome.columns
        ):

            genes_hs = [str(x) for x in self.genome["gene_Homo_sapiens"] if x == x] + [
                "tissue"
            ]

            df = self.get_REF_GEN_RNA_SEQ()

            for k in df.keys():
                tmp = df[k]
                tmp = {key: tmp[key] for key in tmp if key in genes_hs}
                if len(tmp.keys()) == 1:
                    tmp = {}

                df[k] = tmp

            self.RNA_SEQ = df

        else:
            raise ValueError(
                "\nSelect features to enriche first! Use select_features() method..."
            )

    def enriche_specificiti(self):
        """
        This method selects elements from the GEDS database that are included in the Human Protein Atlas (HPA) information.
        It includes specificity to the following categories:
            - HPA_RNA_tissue
            - HPA_RNA_single_cell
            - HPA_RNA_cancer
            - HPA_RNA_brain
            - HPA_RNA_blood
            - HPA_RNA_blood_lineage
            - HPA_RNA_cell_line
            - HPA_RNA_mouse_brain_region
            - HPA_subcellular_location
            - HPA_blood_markers

        Returns:
            Updates `self.HPA` with Human Protein Atlas information.
            To retrieve the results, use the `self.get_HPA` method.
        """

        if (
            isinstance(self.genome, pd.DataFrame)
            and "found_names" in self.genome.columns
        ):
            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            hpa_datasets = [
                "HPA_RNA_tissue",
                "HPA_RNA_single_cell",
                "HPA_RNA_cancer",
                "HPA_RNA_brain",
                "HPA_RNA_blood",
                "HPA_RNA_blood_lineage",
                "HPA_RNA_cell_line",
                "HPA_RNA_mouse_brain_region",
                "HPA_subcellular_location",
                "HPA_blood_markers",
            ]

            ids = [int(x) for x in self.genome["id_HPA"] if x == x]

            full_dict = {}
            for k in hpa_datasets:

                query = f"SELECT * FROM {k} WHERE id IN ({', '.join(map(str, ids))});"

                df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

                df = pd.merge(
                    df,
                    self.genome[["id_HPA", "found_names"]],
                    how="left",
                    left_on="id",
                    right_on="id_HPA",
                )
                df = df.drop(["id_HPA"], axis=1)

                full_dict[k] = df.to_dict(orient="list")

            conn.close()

            self.HPA = full_dict

        else:
            raise ValueError(
                "\nSelect features to enriche first! Use select_features() method..."
            )

    def enriche_KEGG(self):
        """
        This method selects elements from the GEDS database that are included in the Kyoto Encyclopedia of Genes and Genomes (KEGG) information.

        Returns:
            Updates `self.KEGG` with KEGG information.
            To retrieve the results, use the `self.get_KEGG` method.
        """

        if (
            isinstance(self.genome, pd.DataFrame)
            and "found_names" in self.genome.columns
        ):

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            ids = [int(x) for x in self.genome["id_KEGG"] if x == x]

            query = f"SELECT * FROM KEGG WHERE id IN ({', '.join(map(str, ids))});"

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            df = pd.merge(
                df,
                self.genome[["id_KEGG", "found_names"]],
                how="left",
                left_on="id",
                right_on="id_KEGG",
            )
            df = df.drop(["id_KEGG"], axis=1)

            conn.close()

            self.KEGG = df.to_dict(orient="list")

        else:
            raise ValueError(
                "\nSelect features to enriche first! Use select_features() method..."
            )

    def enriche_GOTERM(self):
        """
        This method selects elements from the GEDS database that are included in the GeneOntology (GO-TERM) information.

        Returns:
            Updates `self.GO` with GO-TERM information.
            To retrieve the results, use the `self.get_GO_TERM` method.
        """

        if (
            isinstance(self.genome, pd.DataFrame)
            and "found_names" in self.genome.columns
        ):

            final_dict = {}

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            ids = [int(x) for x in self.genome["id_GO"] if x == x]

            species = self.species_study
            species = ", ".join(map(lambda x: f"'{x}'", species))

            query = f"""SELECT * FROM GO_gene_info 
            WHERE id IN ({', '.join(map(str, ids))})
              AND species IN ({species});
            """

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            df = pd.merge(
                df,
                self.genome[["id_GO", "found_names"]],
                how="left",
                left_on="id",
                right_on="id_GO",
            )
            df = df.drop(["id_GO"], axis=1)

            final_dict["gene_info"] = df.to_dict(orient="list")

            ids = ", ".join(map(lambda x: f"'{x}'", df["GO_id"]))
            hids = list(df["GO_id"])

            query = f"SELECT * FROM GO_go_names WHERE GO_id IN ({ids});"

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            final_dict["go_names"] = df.to_dict(orient="list")

            query = f"SELECT * FROM GO_hierarchy WHERE GO_id IN ({ids});"

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            for cl in [
                "is_a_ids",
                "part_of_ids",
                "has_part_ids",
                "regulates_ids",
                "negatively_regulates_ids",
                "positively_regulates_ids",
            ]:
                tmp_val = [x if x in hids else None for x in df[cl]]
                df[cl] = tmp_val

            final_dict["hierarchy"] = df.to_dict(orient="list")

            del df

            conn.close()

            self.GO_TERM = final_dict

        else:
            raise ValueError(
                "\nSelect features to enriche first! Use select_features() method..."
            )

    def enriche_REACTOME(self):
        """
        This method selects elements from the GEDS database that are included in the Reactome information.

        Returns:
            Updates `self.REACTOME` with Reactome information.
            To retrieve the results, use the `self.get_REACTOME` method.
        """

        if (
            isinstance(self.genome, pd.DataFrame)
            and "found_names" in self.genome.columns
        ):

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            ids = [int(x) for x in self.genome["id_reactome"] if x == x]

            query = f"SELECT * FROM REACTOME WHERE id IN ({', '.join(map(str, ids))});"

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            df = pd.merge(
                df,
                self.genome[["id_reactome", "found_names"]],
                how="left",
                left_on="id",
                right_on="id_reactome",
            )
            df = df.drop(["id_reactome"], axis=1)

            conn.close()

            self.REACTOME = df.to_dict(orient="list")

        else:
            raise ValueError(
                "\nSelect features to enriche first! Use select_features() method..."
            )

    def enriche_DISEASES(self):
        """
        This method selects elements from the GEDS database that are included in the Human Diseases information.

        Returns:
            Updates `self.Diseases` with Human Diseases information.
            To retrieve the results, use the `self.get_DISEASES` method.
        """

        if (
            isinstance(self.genome, pd.DataFrame)
            and "found_names" in self.genome.columns
        ):

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            ids = [int(x) for x in self.genome["id_diseases"] if x == x]

            query = f"SELECT * FROM disease WHERE id IN ({', '.join(map(str, ids))});"

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            df = pd.merge(
                df,
                self.genome[["id_diseases", "found_names"]],
                how="left",
                left_on="id",
                right_on="id_diseases",
            )
            df = df.drop(["id_diseases"], axis=1)

            conn.close()

            self.Diseases = df.to_dict(orient="list")

        else:
            raise ValueError(
                "\nSelect features to enriche first! Use select_features() method..."
            )

    def enriche_ViMIC(self):
        """
        This method selects elements from the GEDS database that are included in the Viral Diseases (ViMIC) information.

        Returns:
            Updates `self.ViMIC` with Viral Disease (ViMIC) information.
            To retrieve the results, use the `self.get_ViMIC` method.
        """

        if (
            isinstance(self.genome, pd.DataFrame)
            and "found_names" in self.genome.columns
        ):

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            ids = [int(x) for x in self.genome["id_viral_diseases"] if x == x]

            query = f"SELECT * FROM ViMIC WHERE id IN ({', '.join(map(str, ids))});"

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            df = pd.merge(
                df,
                self.genome[["id_viral_diseases", "found_names"]],
                how="left",
                left_on="id",
                right_on="id_viral_diseases",
            )
            df = df.drop(["id_viral_diseases"], axis=1)

            conn.close()

            self.ViMIC = df.to_dict(orient="list")

        else:
            raise ValueError(
                "\nSelect features to enriche first! Use select_features() method..."
            )

    def enriche_IntAct(self):
        """
        This method selects elements from the GEDS database that are included in the IntAct information.
        It includes specificity to the following data sets:
            - Affinomics
            - Alzheimers
            - BioCreative
            - Cancer
            - Cardiac
            - Chromatin
            - Coronavirus
            - Cyanobacteria
            - Diabetes
            - Huntington
            - IBD
            - Neurodegeneration
            - Parkinsons
            - Rare Diseases
            - Ulcerative

        Returns:
            Updates `self.IntAct` with IntAct information.
            To retrieve the results, use the `self.get_IntAct` method.
        """

        if (
            isinstance(self.genome, pd.DataFrame)
            and "found_names" in self.genome.columns
        ):

            final_dict = {}

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            ids = [int(x) for x in self.genome["id_IntAct"] if x == x]

            species = self.species_study
            species = ", ".join(map(lambda x: f"'{x}'", species))

            query = f"""
            SELECT * 
            FROM IntAct_gene_product 
            WHERE id_1 IN ({', '.join(map(str, ids))}) 
              AND id_2 IN ({', '.join(map(str, ids))})
              AND species IN ({species});
            """

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            df = pd.merge(
                df,
                self.genome[["id_IntAct", "found_names"]],
                how="left",
                left_on="id_1",
                right_on="id_IntAct",
            )
            df = df.drop(["id_IntAct"], axis=1)
            df = df.rename(columns={"found_names": "found_names_1"})

            df = pd.merge(
                df,
                self.genome[["id_IntAct", "found_names"]],
                how="left",
                left_on="id_2",
                right_on="id_IntAct",
            )
            df = df.drop(["id_IntAct"], axis=1)
            df = df.rename(columns={"found_names": "found_names_2"})

            final_dict["gene_products"] = df.to_dict(orient="list")

            query = f"""
            SELECT * 
            FROM IntAct_non_gene_product 
            WHERE id_1 IN ({', '.join(map(str, ids))}) 
              OR id_2 IN ({', '.join(map(str, ids))})
              AND species IN ({species});
            """

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            final_dict["non_gene_products"] = df.to_dict(orient="list")

            conn.close()

            self.IntAct = final_dict

        else:
            raise ValueError(
                "\nSelect features to enriche first! Use select_features() method..."
            )

    def enriche_STRING(self):
        """
        This method selects elements from the GEDS database that are included in the STRING information.

        Returns:
            Updates `self.STRING` with STRING information.
            To retrieve the results, use the `self.get_STRING` method.
        """

        if (
            isinstance(self.genome, pd.DataFrame)
            and "found_names" in self.genome.columns
        ):

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            ids = [int(x) for x in self.genome["id_STRING"] if x == x]

            species = self.species_study
            species = ", ".join(map(lambda x: f"'{x}'", species))

            query = f"""
            SELECT * 
            FROM STRING 
            WHERE protein1 IN ({', '.join(map(str, ids))}) 
              AND protein2 IN ({', '.join(map(str, ids))})
              AND species IN ({species});
            """

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            df = pd.merge(
                df,
                self.genome[["id_STRING", "found_names"]],
                how="left",
                left_on="protein1",
                right_on="id_STRING",
            )
            df = df.drop(["id_STRING"], axis=1)
            df = df.rename(columns={"found_names": "found_names_1"})

            df = pd.merge(
                df,
                self.genome[["id_STRING", "found_names"]],
                how="left",
                left_on="protein2",
                right_on="id_STRING",
            )
            df = df.drop(["id_STRING"], axis=1)
            df = df.rename(columns={"found_names": "found_names_2"})

            conn.close()

            self.STRING = df.to_dict(orient="list")

        else:
            raise ValueError(
                "\nSelect features to enriche first! Use select_features() method..."
            )

    def enriche_CellCon(self):
        """
        This method selects elements from the GEDS database that are included in the CellPhone / CellTalk information.

        Returns:
            Updates `self.CellCon` with CellPhone / CellTalk information.
            To retrieve the results, use the `self.get_CellCon` method.
        """

        if (
            isinstance(self.genome, pd.DataFrame)
            and "found_names" in self.genome.columns
        ):

            tmp = {}
            ###################################################################

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            ids = [int(x) for x in self.genome["id_cell_int"] if x == x]

            species = self.species_study
            species = ", ".join(map(lambda x: f"'{x}'", species))

            query = f"""
            SELECT * 
            FROM CellInteractions 
            WHERE protein_id_2 IN ({', '.join(map(str, ids))})
              AND Species IN ({species});
            """

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            df = pd.merge(
                df,
                self.genome[["id_cell_int", "found_names"]],
                how="left",
                left_on="protein_id_1",
                right_on="id_cell_int",
            )
            df = df.drop(["id_cell_int"], axis=1)
            df = df.rename(columns={"found_names": "found_names_1"})

            df = pd.merge(
                df,
                self.genome[["id_cell_int", "found_names"]],
                how="left",
                left_on="protein_id_2",
                right_on="id_cell_int",
            )
            df = df.drop(["id_cell_int"], axis=1)
            df = df.rename(columns={"found_names": "found_names_2"})

            tmp["interactor1"] = df.to_dict(orient="list")
            ###################################################################

            query = f"""
            SELECT * 
            FROM CellInteractions 
            WHERE protein_id_1 IN ({', '.join(map(str, ids))}) 
              AND Species IN ({species});
            """

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            df = pd.merge(
                df,
                self.genome[["id_cell_int", "found_names"]],
                how="left",
                left_on="protein_id_1",
                right_on="id_cell_int",
            )
            df = df.drop(["id_cell_int"], axis=1)
            df = df.rename(columns={"found_names": "found_names_1"})

            df = pd.merge(
                df,
                self.genome[["id_cell_int", "found_names"]],
                how="left",
                left_on="protein_id_2",
                right_on="id_cell_int",
            )
            df = df.drop(["id_cell_int"], axis=1)
            df = df.rename(columns={"found_names": "found_names_2"})

            tmp["interactor2"] = df.to_dict(orient="list")

            ###################################################################

            query = f"""
            SELECT * 
            FROM CellInteractions 
            WHERE protein_id_1 IN ({', '.join(map(str, ids))}) 
              AND protein_id_2 IN ({', '.join(map(str, ids))})
              AND Species IN ({species});
            """

            df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            df = pd.merge(
                df,
                self.genome[["id_cell_int", "found_names"]],
                how="left",
                left_on="protein_id_1",
                right_on="id_cell_int",
            )
            df = df.drop(["id_cell_int"], axis=1)
            df = df.rename(columns={"found_names": "found_names_1"})

            df = pd.merge(
                df,
                self.genome[["id_cell_int", "found_names"]],
                how="left",
                left_on="protein_id_2",
                right_on="id_cell_int",
            )
            df = df.drop(["id_cell_int"], axis=1)
            df = df.rename(columns={"found_names": "found_names_2"})

            tmp["mutual"] = df.to_dict(orient="list")

            conn.close()

            self.CellCon = tmp

        else:
            raise ValueError(
                "\nSelect features to enriche first! Use select_features() method..."
            )

    def select_features(self, features_list: list):
        """
        This method searches for the occurrence of genes or proteins in the GEDS database.
        Available names include those from HGNC, Ensembl, or NCBI gene names or IDs,
        for the species Homo sapiens, Mus musculus, or Rattus norvegicus.

        Args:
            features_list (list) - list of features (gene or protein names or IDs)

        Returns:
            Updates `self.genome` with feature information found in the GEDS database

        """

        self.features_list = self.reduce_extended_gtf(features_list)

        self.load_genome()
        self.spec_dic()

        print("\nFeatures selection...")

        self.find_fetures_id()
        self.v1_is_in_v2()
        self.return_dictionary()
        self.add_found_names()

        nf = self.show_non_founded_features()

        if len(nf) > 0:
            print("\nSome features were not found in Database:")
            for n in nf:
                print(f" --> {n}")

    def full_enrichment(self):
        """
        This method conducts a full enrichment analysis based on the GEDS database, which includes:
            - Human Protein Atlas (HPA) [see self.enriche_specificiti() method]
            - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see self.enriche_KEGG() method]
            - GeneOntology (GO-TERM) [see self.enriche_GOTERM() method]
            - Reactome [see self.enriche_REACTOME() method]
            - Human Diseases [see self.enriche_DISEASES() method]
            - Viral Diseases (ViMIC) [see self.enriche_ViMIC() method]
            - IntAct [see self.enriche_IntAct() method]
            - STRING [see self.enriche_STRING() method]
            - CellConnections (CellPhone / CellTalk) [see self.enriche_CellCon() method]
            - RNAseq data specific to tissues [see self.enriche_RNA_SEQ() method]

        Returns:
            To retrieve the results, use the `self.get_results` method.

        """

        if (
            isinstance(self.genome, pd.DataFrame)
            and "found_names" in self.genome.columns
        ):

            print("\nSpecificity enrichment...")

            self.enriche_specificiti()

            print("\nEnrichment with KEGG information...")

            self.enriche_KEGG()

            print("\nEnrichment with GO-TERM information...")

            self.enriche_GOTERM()

            print("\nEnrichment with REACTOME information...")

            self.enriche_REACTOME()

            print("\nEnrichment with DISEASES information...")

            self.enriche_DISEASES()

            print("\nEnrichment with ViMIC information...")

            self.enriche_ViMIC()

            print("\nEnrichment with IntAct information...")

            self.enriche_IntAct()

            print("\nEnrichment with STRING information...")

            self.enriche_STRING()

            print("\nEnrichment with CellConnections information...")

            self.enriche_CellCon()

            print("\nEnrichment with tissue specific RNA-SEQ information...")

            self.enriche_RNA_SEQ()

        else:
            raise ValueError(
                "\nSelect features to enriche first! Use select_features() method..."
            )


class Analysis(Enrichment):
    """
    The `Analysis` class provides tools for statistical and network analysis of `Enrichment` class results obtained using the `self.get_results` method.

    Args:
        input_data (dict) - output data from the `Enrichment` class `self.get_results` method

    """

    def __init__(self, input_data: dict):

        self.input_data = input_data
        self.KEGG_stat = None
        self.GO_stat = None
        self.REACTOME_stat = None
        self.DISEASE_stat = None
        self.ViMIC_stat = None
        self.features_interactions = None
        self.specificity_stat = None
        self.KEGG_net = None
        self.GO_net = None
        self.REACTOME_net = None
        self.network_stat = {
            "test": "FISH",
            "adj": "BH",
            "p_val": 0.05,
            "parent_stat": False,
        }
        self.go_grade = 1
        self.occ = None
        self.interaction_strength = 900
        self.interaction_source = [
            "Affinomics",
            "Alzheimers",
            "BioCreative",
            "Cancer",
            "Cardiac",
            "Chromatin",
            "Coronavirus",
            "Diabetes",
            "Huntington's",
            "IBD",
            "Neurodegeneration",
            "Parkinsons",
            "STRING",
        ]

        super().__init__()

    def interactions_metadata(self):
        """
        This method returns current interactions parameters:

            -interaction_strength : int - value of enrichment strenght for STRING data:
                *900 - very high probabylity of interaction;
                *700 - medium probabylity of interaction,
                *400 - low probabylity of interaction,
                *<400 - very low probabylity of interaction


            -interaction_source : list - list of sources for interaction estimation:
                *STRING: ['STRING']
                *IntAct: ['Affinomics', 'Alzheimers','BioCreative', 'Cancer',
                          'Cardiac', 'Chromatin', 'Coronavirus', 'Diabetes',
                          "Huntington's", 'IBD', 'Neurodegeneration', 'Parkinsons']


        Returns:
            dict : {'interaction_strength' : int,
                    'interaction_source' : list}

        """

        return {
            "interaction_strength": self.interaction_strength,
            "interaction_source": self.interaction_source,
        }

    def set_interaction_strength(self, value: int):
        """
        This method sets self.interaction_strength parameter.

        The 'interaction_strength' value is used for enrichment strenght of STRING data:
             *900 - very high probabylity of interaction;
             *700 - medium probabylity of interaction,
             *400 - low probabylity of interaction,
             *<400 - very low probabylity of interaction

        Args:
            value (int) - value of interaction strength

        """

        if value < 1000 and value > 0:
            self.interaction_strength = value

        else:

            raise ValueError("\nValue should be integer between 0 and 1000")

    def set_go_grade(self, grade: int):
        """
        This method sets self.go_grade parameter.

        The 'go_grade' value is used for GO-TERM data gradation [1-4].

            Args:
                grade (int) - grade level for GO terms analysis. Default: 1

        """

        if grade < 5 and grade > 0:
            self.go_grade = grade

        else:

            raise ValueError("\nValue should be integer between 0 and 1000")

    def set_interaction_source(self, sources_list: list):
        """
        This method sets self.interaction_source parameter.

        The 'interaction_source' value is list of sources for interaction estimation:

            *STRING / IntAct: ['STRING', 'Affinomics', 'Alzheimers','BioCreative',
                               'Cancer', 'Cardiac', 'Chromatin', 'Coronavirus',
                               'Diabetes', "Huntington's", 'IBD', 'Neurodegeneration',
                               'Parkinsons']

        Args:
            sources_list (list) - list of source data for interactions network analysis

        """

        values = [
            "STRING",
            "Affinomics",
            "Alzheimers",
            "BioCreative",
            "Cancer",
            "Cardiac",
            "Chromatin",
            "Coronavirus",
            "Diabetes",
            "Huntington's",
            "IBD",
            "Neurodegeneration",
            "Parkinsons",
        ]

        if all(value in values for value in sources_list):
            self.interaction_source = sources_list

        else:

            raise ValueError(
                "\nValues in list should be included in STRING, Affinomics, Alzheimers, BioCreative, Cancer, Cardiac, Chromatin, Coronavirus, Diabetes, Huntington`s, IBD, Neurodegeneration, Parkinsons"
            )

    def networks_metadata(self):
        """
        This method returns current networks creation parameters:

            -test : str - test type for enrichment overrepresentation analysis.
                Available test:
                    *BIN - binomial test
                    *FISH - Fisher's exact test

            -adj : str | None - p_value correction.
                Available correction:
                    *BF - Bonferroni correction
                    *BH - Benjamini-Hochberg correction
                    *None - lack of correction

            -p_val : float - threshold for p-value in network creation


        Returns:
            dict : {'test': str,
                    'adj': str | None,
                    'p_val': float}

        """

        return self.network_stat

    def set_p_value(self, value: float):
        """
        This method sets the p-value threshold for network creation

            Args:
                value (float) - p-value threshold for network creation
        """

        if value > 0 and value < 1:
            self.network_stat["p_val"] = value

        else:

            raise ValueError("\nValue should be float between 0 and 1")

    def set_test(self, test):
        """
        This method sets the statistical test to be used for network creation.

            Avaiable tests:
                - 'FISH' - Fisher's exact test
                - 'BIN' - Binomial test

            Args:
                test (str) - test acronym ['FISH'/'BIN']
        """

        if test.upper() == "FISH" or test.upper() == "BIN":
            self.network_stat["test"] = test.upper()

        else:

            raise ValueError("\nTest should be included in BIN or FISH")

    def set_parent_stats(self, stats):
        """
        This method sets the parent statistical test value used for network creation.

            Avaiable values:
                - True - use test p-value for drop non-significient parents
                - False - not use test p-value for drop non-significient parents

            Args:
                test (bool) - bool value [True/False]
        """

        if stats in [True, False]:
            self.network_stat["parent_stat"] = stats

        else:

            raise ValueError("\nStats should be included in True or False")

    def set_correction(self, correction):
        """
        This method sets the statistical test correction to be used for network creation.

            Avaiable tests:
                - 'BF' - Bonferroni correction
                - 'BH' - Benjamini-Hochberg correction
                - None - lack of correction

            Args:
                correction (str / None) - test correction acronym ['BF'/'BH'/None]
        """

        if correction is None:
            self.network_stat["adj"] = None

        else:

            if correction.upper() == "BF" or correction.upper() == "BH":
                self.network_stat["adj"] = correction.upper()

            else:

                raise ValueError("\nTest should be included in BF or BH")

    def get_KEGG_statistics(self):
        """
        This method returns the KEGG overrepresentation statistics.

        Returns:
            Returns `self.KEGG_stat` contains KEGG overrepresentation statistics obtained using the `self.KEGG_overrepresentation` method.
        """

        if self.KEGG_stat != None:

            return self.KEGG_stat

        else:
            raise ValueError("\nNo data to return...")

    def get_REACTOME_statistics(self):
        """
        This method returns the Reactome overrepresentation statistics.

        Returns:
            Returns `self.REACTOME_stat` contains Reactome overrepresentation statistics obtained using the `self.REACTOME_overrepresentation` method.
        """

        if self.REACTOME_stat != None:

            return self.REACTOME_stat

        else:
            raise ValueError("\nNo data to return...")

    def get_GO_statistics(self):
        """
        This method returns the GO-TERM overrepresentation statistics.

        Returns:
            Returns `self.GO_stat` contains GO-TERM overrepresentation statistics obtained using the `self.GO_overrepresentation` method.
        """

        if self.GO_stat != None:

            return self.GO_stat

        else:
            raise ValueError("\nNo data to return...")

    def get_DISEASE_statistics(self):
        """
        This method returns the Human Diseases overrepresentation statistics.

        Returns:
            Returns `self.DISEASE_stat` contains Human Diseases overrepresentation statistics obtained using the `self.DISEASES_overrepresentation` method.
        """

        if self.DISEASE_stat != None:

            return self.DISEASE_stat

        else:
            raise ValueError("\nNo data to return...")

    def get_ViMIC_statistics(self):
        """
        This method returns the ViMIC overrepresentation statistics.

        Returns:
            Returns `self.ViMIC_stat` contains ViMIC overrepresentation statistics obtained using the `self.ViMIC_overrepresentation` method.
        """

        if self.ViMIC_stat != None:

            return self.ViMIC_stat

        else:
            raise ValueError("\nNo data to return...")

    def get_features_interactions_statistics(self):
        """
        This method returns the Genes Interactions (GI) data.

        Returns:
            Returns `self.features_interactions` contains GI data obtained using the `self.gene_interaction` method.
        """

        if self.features_interactions != None:

            return self.features_interactions

        else:
            raise ValueError("\nNo data to return...")

    def get_specificity_statistics(self):
        """
        This method returns the tissue specificity [Human Protein Atlas (HPA)] overrepresentation statistics.

        Returns:
            Returns `self.specificity_stat` contains specificity overrepresentation statistics obtained using the `self.features_specificity` method.
        """

        if self.specificity_stat != None:

            return self.specificity_stat

        else:
            raise ValueError("\nNo data to return...")

    def get_KEGG_network(self):
        """
        This method returns the KEGG network analysis results.

        Returns:
            Returns `self.KEGG_net` contains KEGG network analysis results obtained using the `self.KEGG_network` method.
        """

        if self.KEGG_net != None:

            return self.KEGG_net

        else:
            raise ValueError("\nNo data to return...")

    def get_REACTOME_network(self):
        """
        This method returns the Reactome network analysis results.

        Returns:
            Returns `self.REACTOME_net` contains Reactome network analysis results obtained using the `self.REACTOME_network` method.
        """

        if self.REACTOME_net != None:

            return self.REACTOME_net

        else:
            raise ValueError("\nNo data to return...")

    def get_GO_network(self):
        """
        This method returns the GO-TERM network analysis results.

        Returns:
            Returns `self.GO_net` contains Reactome network analysis results obtained using the `self.GO_network` method.
        """

        if self.GO_net != None:

            return self.GO_net

        else:
            raise ValueError("\nNo data to return...")

    def map_interactions_flat(self, row, mapping):
        interactions = [typ for col in row if col in mapping for typ in mapping[col]]
        return list(set(interactions))

    def select_test(self, test, adj):
        try:
            test_string = ""

            if adj != None and adj.upper() in ["BF", "BH"]:
                test_string = test_string + "adj_pval_"
            else:
                test_string = test_string + "pval_"

            if test != None and test.upper() == "BIN":
                test_string = test_string + "BIN"
            elif test != None and test.upper() == "FISH":
                test_string = test_string + "FISH"
            else:
                test_string = test_string + "BIN"

            if adj != None and adj.upper() == "BF":
                test_string = test_string + "-BF"
            elif adj != None and adj.upper() == "BH":
                test_string = test_string + "-BH"
            else:
                test_string = test_string + ""

            return test_string
        except:
            print("\n")
            print("Provided wrong test input!")

    def run_enrichment_tests(self, N, K, n, k):

        fisher_table = [[k, K - k], [n - k, N - K - (n - k)]]

        fisher_odds_ratio, fisher_p_value = fisher_exact(
            fisher_table, alternative="greater"
        )

        p_background = K / N

        binomial_p_value = binomtest(k, n, p=p_background, alternative="greater").pvalue

        return {
            "fisher_p_value": fisher_p_value,
            "fisher_odds_ratio": fisher_odds_ratio,
            "binomial_p_value": binomial_p_value,
        }

    def create_full_conections(self, go_data, grade=1):

        go_data = go_data[
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

        for i in [
            "is_a_ids",
            "part_of_ids",
            "has_part_ids",
            "regulates_ids",
            "negatively_regulates_ids",
            "positively_regulates_ids",
        ]:

            go_data = go_data.explode(i)

        go_wide = pd.DataFrame()

        init_list = list(set(go_data["GO_id"][go_data["is_a_ids"].isin([None])]))
        full_list = list(set(go_data["GO_id"][~go_data["is_a_ids"].isin([None])]))

        for i in [
            "is_a_ids",
            "part_of_ids",
            "has_part_ids",
            "regulates_ids",
            "negatively_regulates_ids",
            "positively_regulates_ids",
        ]:

            go_tmp = go_data[["GO_id", i]][go_data[i].isin(init_list)]
            go_tmp.columns = ["grade_1", "parent"]

            go_wide = pd.concat([go_wide, go_tmp])

        final_wide = go_wide.copy()
        final_wide = final_wide.drop("parent", axis=1)

        grade_set = set(go_wide["grade_1"])

        grade_dict = {}

        n = 1
        while True:

            # print(f'Round {n}')

            if len(full_list) == 0:
                break

            go_wide_tmp = pd.DataFrame()

            full_list = [x for x in full_list if x not in grade_set]

            for i in [
                "is_a_ids",
                "part_of_ids",
                "has_part_ids",
                "regulates_ids",
                "negatively_regulates_ids",
                "positively_regulates_ids",
            ]:

                go_tmp = go_data[["GO_id", i]][go_data[i].isin(grade_set)]
                go_tmp.columns = [f"grade_{n+1}", "parent2"]

                go_wide_tmp = pd.concat([go_wide_tmp, go_tmp])

            if len(go_wide_tmp.index) == 0:
                break

            final_wide = pd.merge(
                final_wide,
                go_wide_tmp,
                left_on=f"grade_{n}",
                right_on="parent2",
                how="left",
            )
            final_wide = final_wide.drop("parent2", axis=1)

            grade_dict[f"grade_1_grade_{n+1}"] = (
                final_wide.groupby("grade_1")
                .agg({f"grade_{n+1}": set})
                .reset_index()
                .copy()
            )

            if n != 1:
                final_wide = final_wide.drop(f"grade_{n}", axis=1).drop_duplicates()

            n += 1

            grade_set = set(go_wide_tmp[f"grade_{n}"])

        primary = None
        for n, i in enumerate(grade_dict.keys()):

            if n + 1 == grade:
                primary = grade_dict[i].reset_index(drop=True)
            else:
                if isinstance(primary, pd.DataFrame):
                    secondary = grade_dict[i].reset_index(drop=True)

                    for inx in primary.index:
                        go_name = primary.iloc[inx, 0]
                        set1_cleaned = (
                            secondary[secondary.iloc[:, 0] == go_name]
                            .reset_index(drop=True)
                            .iloc[0, 1]
                        )
                        set1_cleaned = {x for x in set1_cleaned if x == x}

                        set2_cleaned = (
                            primary[primary.iloc[:, 0] == go_name]
                            .reset_index(drop=True)
                            .iloc[0, 1]
                        )
                        set2_cleaned = {x for x in set2_cleaned if x == x}

                        set1_cleaned = set1_cleaned | set2_cleaned

                        if len(set1_cleaned) == 0:
                            set1_cleaned = {}

                        primary.iloc[inx, 1] = list(set1_cleaned)

        primary.columns = ["parent", "children"]

        primary = primary.explode("children")

        return primary.reset_index(drop=True)

    def GO_overrepresentation(self):
        """
        This method conducts an overrepresentation analysis of Gene Ontology (GO-TERM) information.

        Returns:
            Updates `self.GO_stat` with overrepresentation statistics for GO-TERM information.
            To retrieve the results, use the `self.get_GO_statistics` method.
        """

        if "GO-TERM" in self.input_data.keys():

            if self.occ is None:
                with open(
                    os.path.join(self.path_in_inside, "occ_dict.json"), "r"
                ) as json_file:
                    self.occ = json.load(json_file)

            go1 = pd.DataFrame(self.input_data["GO-TERM"]["gene_info"])
            go2 = pd.DataFrame(self.input_data["GO-TERM"]["go_names"])

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            query = "SELECT * FROM GO_hierarchy;"

            hierarchy = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

            results = self.create_full_conections(hierarchy, grade=self.go_grade)

            for i in results.index:

                if (
                    results.iloc[i, 0] == results.iloc[i, 0]
                    and results.iloc[i, 1] != results.iloc[i, 1]
                ):

                    results.iloc[i, 1] = results.iloc[i, 0]

                    results.iloc[i, 0] = "Core group"

            go3 = pd.merge(go1, go2, on="GO_id", how="left")

            results = results[
                results.iloc[:, 0].isin(list(go3["GO_id"]) + ["Core group"])
            ]
            results = results[results.iloc[:, 1].isin(list(go3["GO_id"]))]

            del go1, go2

            go_out = {}

            go_out["parent"] = []
            go_out["parent_genes"] = []
            go_out["parent_pval_FISH"] = []
            go_out["parent_pval_BIN"] = []
            go_out["parent_n"] = []
            go_out["parent_pct"] = []

            go_out["child"] = []
            go_out["child_genes"] = []
            go_out["child_pval_FISH"] = []
            go_out["child_pval_BIN"] = []
            go_out["child_n"] = []
            go_out["child_pct"] = []

            species = self.input_data["species"]["species_study"]
            species = ", ".join(map(lambda x: f"'{x}'", species))

            for i in tqdm(set(results["parent"])):

                if i != "Core group":

                    query = f"""SELECT * FROM GO_gene_info 
                            WHERE GO_id IN ('{i}')
                              AND species IN ({species});
                            """

                    df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

                    res = self.run_enrichment_tests(
                        N=self.occ["Genes_Homo_sapiens"],
                        K=len(set(df["id"])),
                        n=len(set(self.input_data["gene_info"]["sid"])),
                        k=len(set(go3["id"][go3["GO_id"] == i])),
                    )

                    for c in set(results["children"][results["parent"].isin([i])]):

                        query = f"""SELECT * FROM GO_gene_info 
                                WHERE GO_id IN ('{c}')
                                  AND species IN ({species});
                                """
                        df = pd.read_sql_query(query, conn).applymap(
                            self.deserialize_data
                        )

                        res2 = self.run_enrichment_tests(
                            N=self.occ["Genes_Homo_sapiens"],
                            K=len(set(df["id"][df["GO_id"] == c])),
                            n=len(set(self.input_data["gene_info"]["sid"])),
                            k=len(set(go3["id"][go3["GO_id"] == c])),
                        )

                        go_out["parent"].append(i)
                        go_out["parent_genes"].append(
                            list(set(go3["found_names"][go3["GO_id"] == i]))
                        )
                        go_out["parent_pval_FISH"].append(res["fisher_p_value"])
                        go_out["parent_pval_BIN"].append(res["binomial_p_value"])
                        go_out["parent_n"].append(
                            len(set(go3["id"][go3["GO_id"] == i]))
                        )
                        go_out["parent_pct"].append(
                            len(set(go3["id"][go3["GO_id"] == i]))
                            / len(set(self.input_data["gene_info"]["sid"]))
                        )

                        go_out["child"].append(c)
                        go_out["child_genes"].append(
                            list(set(go3["found_names"][go3["GO_id"] == c]))
                        )
                        go_out["child_pval_FISH"].append(res2["fisher_p_value"])
                        go_out["child_pval_BIN"].append(res2["binomial_p_value"])
                        go_out["child_n"].append(len(set(go3["id"][go3["GO_id"] == c])))
                        go_out["child_pct"].append(
                            len(set(go3["id"][go3["GO_id"] == c]))
                            / len(set(self.input_data["gene_info"]["sid"]))
                        )

                else:

                    for c in set(results["children"][results["parent"].isin([i])]):

                        query = f"""SELECT * FROM GO_gene_info 
                                WHERE GO_id IN ('{c}')
                                  AND species IN ({species});
                                """
                        df = pd.read_sql_query(query, conn).applymap(
                            self.deserialize_data
                        )

                        res2 = self.run_enrichment_tests(
                            N=self.occ["Genes_Homo_sapiens"],
                            K=len(set(df["id"][df["GO_id"] == c])),
                            n=len(set(self.input_data["gene_info"]["sid"])),
                            k=len(set(go3["id"][go3["GO_id"] == c])),
                        )

                        go_out["parent"].append(i)
                        go_out["parent_genes"].append(
                            list(
                                set(
                                    go3["found_names"][
                                        go3["GO_id"].isin(
                                            set(
                                                results["children"][
                                                    results["parent"] == i
                                                ]
                                            )
                                        )
                                    ]
                                )
                            )
                        )
                        go_out["parent_pval_FISH"].append(0)
                        go_out["parent_pval_BIN"].append(0)
                        go_out["parent_n"].append(
                            len(
                                set(
                                    go3["found_names"][
                                        go3["GO_id"].isin(
                                            set(
                                                results["children"][
                                                    results["parent"] == i
                                                ]
                                            )
                                        )
                                    ]
                                )
                            )
                        )
                        go_out["parent_pct"].append(
                            len(
                                set(
                                    go3["found_names"][
                                        go3["GO_id"].isin(
                                            set(
                                                results["children"][
                                                    results["parent"] == i
                                                ]
                                            )
                                        )
                                    ]
                                )
                            )
                            / len(set(self.input_data["gene_info"]["sid"]))
                        )

                        go_out["child"].append(c)
                        go_out["child_genes"].append(
                            list(set(go3["found_names"][go3["GO_id"] == c]))
                        )
                        go_out["child_pval_FISH"].append(res2["fisher_p_value"])
                        go_out["child_pval_BIN"].append(res2["binomial_p_value"])
                        go_out["child_n"].append(len(set(go3["id"][go3["GO_id"] == c])))
                        go_out["child_pct"].append(
                            len(set(go3["id"][go3["GO_id"] == c]))
                            / len(set(self.input_data["gene_info"]["sid"]))
                        )

            go_out = pd.DataFrame(go_out)

            # parent adjustment
            go_out["parent_adj_pval_BIN-BF"] = go_out["parent_pval_BIN"] * len(
                go_out["parent_pval_BIN"]
            )
            go_out["parent_adj_pval_BIN-BF"][go_out["parent_adj_pval_BIN-BF"] >= 1] = 1
            go_out["parent_adj_pval_FISH-BF"] = go_out["parent_pval_FISH"] * len(
                go_out["parent_pval_FISH"]
            )
            go_out["parent_adj_pval_FISH-BF"][
                go_out["parent_adj_pval_FISH-BF"] >= 1
            ] = 1

            go_out = go_out.sort_values(by="parent_pval_BIN", ascending=True)

            n = len(go_out["parent_pval_BIN"])

            go_out["parent_adj_pval_BIN-BH"] = (
                go_out["parent_pval_BIN"] * n
            ) / np.arange(1, n + 1)

            go_out = go_out.sort_values(by="parent_pval_FISH", ascending=True)

            go_out["parent_adj_pval_FISH-BH"] = (
                go_out["parent_pval_FISH"] * n
            ) / np.arange(1, n + 1)

            go_out["parent_adj_pval_FISH-BH"][
                go_out["parent_adj_pval_FISH-BH"] >= 1
            ] = 1
            go_out["parent_adj_pval_BIN-BH"][go_out["parent_adj_pval_BIN-BH"] >= 1] = 1

            # child adjustment
            go_out["child_adj_pval_BIN-BF"] = go_out["child_pval_BIN"] * len(
                go_out["child_pval_BIN"]
            )
            go_out["child_adj_pval_BIN-BF"][go_out["child_adj_pval_BIN-BF"] >= 1] = 1
            go_out["child_adj_pval_FISH-BF"] = go_out["child_pval_FISH"] * len(
                go_out["child_pval_FISH"]
            )
            go_out["child_adj_pval_FISH-BF"][go_out["child_adj_pval_FISH-BF"] >= 1] = 1

            go_out = go_out.sort_values(by="child_pval_BIN", ascending=True)

            n = len(go_out["child_pval_BIN"])

            go_out["child_adj_pval_BIN-BH"] = (
                go_out["child_pval_BIN"] * n
            ) / np.arange(1, n + 1)

            go_out = go_out.sort_values(by="child_pval_FISH", ascending=True)

            go_out["child_adj_pval_FISH-BH"] = (
                go_out["child_pval_FISH"] * n
            ) / np.arange(1, n + 1)

            go_out["child_adj_pval_FISH-BH"][go_out["child_adj_pval_FISH-BH"] >= 1] = 1
            go_out["child_adj_pval_BIN-BH"][go_out["child_adj_pval_BIN-BH"] >= 1] = 1

            conn.close()

            gn = pd.DataFrame(self.input_data["GO-TERM"]["go_names"])

            name_mapping = dict(zip(gn["GO_id"], gn["name"]))
            go_out["parent_name"] = go_out["parent"].map(name_mapping)
            go_out["child_name"] = go_out["child"].map(name_mapping)

            del gn

            self.GO_stat = go_out.to_dict(orient="list")

        else:
            print(
                "\nGO enrichment analysis could not be performed due to missing GO information in the input data."
            )

    def KEGG_overrepresentation(self):
        """
        This method conducts an overrepresentation analysis of Kyoto Encyclopedia of Genes and Genomes (KEGG) information.

        Returns:
            Updates `self.KEGG_stat` with overrepresentation statistics for KEGG information.
            To retrieve the results, use the `self.get_KEGG_statistics` method.
        """

        if "KEGG" in self.input_data.keys():

            if self.occ is None:
                with open(
                    os.path.join(self.path_in_inside, "occ_dict.json"), "r"
                ) as json_file:
                    self.occ = json.load(json_file)

            kegg_out = {}
            kegg = pd.DataFrame(self.input_data["KEGG"])

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            kegg_out["2nd"] = []
            kegg_out["2nd_genes"] = []
            kegg_out["2nd_pval_FISH"] = []
            kegg_out["2nd_pval_BIN"] = []
            kegg_out["2nd_n"] = []
            kegg_out["2nd_pct"] = []

            kegg_out["3rd"] = []
            kegg_out["3rd_genes"] = []
            kegg_out["3rd_pval_FISH"] = []
            kegg_out["3rd_pval_BIN"] = []
            kegg_out["3rd_n"] = []
            kegg_out["3rd_pct"] = []

            for i in tqdm(set(kegg["2nd"])):

                query = f'SELECT * FROM KEGG WHERE "2nd" IN ("{i}");'

                df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

                res = self.run_enrichment_tests(
                    N=self.occ["Genes_Homo_sapiens"],
                    K=len(set(df["id"])),
                    n=len(set(self.input_data["gene_info"]["sid"])),
                    k=len(set(kegg["id"][kegg["2nd"] == i])),
                )

                for c in set(kegg["3rd"][kegg["2nd"].isin([i])]):

                    res2 = self.run_enrichment_tests(
                        N=self.occ["Genes_Homo_sapiens"],
                        K=len(set(df["id"][df["3rd"] == c])),
                        n=len(set(self.input_data["gene_info"]["sid"])),
                        k=len(set(kegg["id"][kegg["3rd"] == c])),
                    )

                    kegg_out["2nd"].append(i)
                    kegg_out["2nd_genes"].append(
                        list(set(kegg["found_names"][kegg["2nd"] == i]))
                    )
                    kegg_out["2nd_pval_FISH"].append(res["fisher_p_value"])
                    kegg_out["2nd_pval_BIN"].append(res["binomial_p_value"])
                    kegg_out["2nd_n"].append(len(set(kegg["id"][kegg["2nd"] == i])))
                    kegg_out["2nd_pct"].append(
                        len(set(kegg["id"][kegg["2nd"] == i]))
                        / len(set(self.input_data["gene_info"]["sid"]))
                    )

                    kegg_out["3rd"].append(c)
                    kegg_out["3rd_genes"].append(
                        list(set(kegg["found_names"][kegg["3rd"] == c]))
                    )
                    kegg_out["3rd_pval_FISH"].append(res2["fisher_p_value"])
                    kegg_out["3rd_pval_BIN"].append(res2["binomial_p_value"])
                    kegg_out["3rd_n"].append(len(set(kegg["id"][kegg["3rd"] == c])))
                    kegg_out["3rd_pct"].append(
                        len(set(kegg["id"][kegg["3rd"] == c]))
                        / len(set(self.input_data["gene_info"]["sid"]))
                    )

            kegg_out = pd.DataFrame(kegg_out)

            # 2nd adjustment
            kegg_out["2nd_adj_pval_BIN-BF"] = kegg_out["2nd_pval_BIN"] * len(
                kegg_out["2nd_pval_BIN"]
            )
            kegg_out["2nd_adj_pval_BIN-BF"][kegg_out["2nd_adj_pval_BIN-BF"] >= 1] = 1
            kegg_out["2nd_adj_pval_FISH-BF"] = kegg_out["2nd_pval_FISH"] * len(
                kegg_out["2nd_pval_FISH"]
            )
            kegg_out["2nd_adj_pval_FISH-BF"][kegg_out["2nd_adj_pval_FISH-BF"] >= 1] = 1

            kegg_out = kegg_out.sort_values(by="2nd_pval_BIN", ascending=True)

            n = len(kegg_out["2nd_pval_BIN"])

            kegg_out["2nd_adj_pval_BIN-BH"] = (
                kegg_out["2nd_pval_BIN"] * n
            ) / np.arange(1, n + 1)

            kegg_out = kegg_out.sort_values(by="2nd_pval_FISH", ascending=True)

            kegg_out["2nd_adj_pval_FISH-BH"] = (
                kegg_out["2nd_pval_FISH"] * n
            ) / np.arange(1, n + 1)

            kegg_out["2nd_adj_pval_FISH-BH"][kegg_out["2nd_adj_pval_FISH-BH"] >= 1] = 1
            kegg_out["2nd_adj_pval_BIN-BH"][kegg_out["2nd_adj_pval_BIN-BH"] >= 1] = 1

            # 3rd adjustment
            kegg_out["3rd_adj_pval_BIN-BF"] = kegg_out["3rd_pval_BIN"] * len(
                kegg_out["3rd_pval_BIN"]
            )
            kegg_out["3rd_adj_pval_BIN-BF"][kegg_out["3rd_adj_pval_BIN-BF"] >= 1] = 1
            kegg_out["3rd_adj_pval_FISH-BF"] = kegg_out["3rd_pval_FISH"] * len(
                kegg_out["3rd_pval_FISH"]
            )
            kegg_out["3rd_adj_pval_FISH-BF"][kegg_out["3rd_adj_pval_FISH-BF"] >= 1] = 1

            kegg_out = kegg_out.sort_values(by="3rd_pval_BIN", ascending=True)

            n = len(kegg_out["3rd_pval_BIN"])

            kegg_out["3rd_adj_pval_BIN-BH"] = (
                kegg_out["3rd_pval_BIN"] * n
            ) / np.arange(1, n + 1)

            kegg_out = kegg_out.sort_values(by="3rd_pval_FISH", ascending=True)

            kegg_out["3rd_adj_pval_FISH-BH"] = (
                kegg_out["3rd_pval_FISH"] * n
            ) / np.arange(1, n + 1)

            kegg_out["3rd_adj_pval_FISH-BH"][kegg_out["3rd_adj_pval_FISH-BH"] >= 1] = 1
            kegg_out["3rd_adj_pval_BIN-BH"][kegg_out["3rd_adj_pval_BIN-BH"] >= 1] = 1

            conn.close()

            self.KEGG_stat = kegg_out.to_dict(orient="list")

        else:
            print(
                "\nKEGG enrichment analysis could not be performed due to missing KEGG information in the input data."
            )

    def REACTOME_overrepresentation(self):
        """
        This method conducts an overrepresentation analysis of Reactome information.

        Returns:
            Updates `self.REACTOME_stat` with overrepresentation statistics for Reactome information.
            To retrieve the results, use the `self.get_REACTOME_statistics` method.
        """

        if "REACTOME" in self.input_data.keys():

            if self.occ is None:
                with open(
                    os.path.join(self.path_in_inside, "occ_dict.json"), "r"
                ) as json_file:
                    self.occ = json.load(json_file)

            reactome_out = {}
            reactome = pd.DataFrame(self.input_data["REACTOME"])

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            reactome_out["pathway"] = []
            reactome_out["pathway_genes"] = []
            reactome_out["complex"] = []
            reactome_out["pathway_pval_FISH"] = []
            reactome_out["pathway_pval_BIN"] = []
            reactome_out["pathway_n"] = []
            reactome_out["pathway_pct"] = []

            reactome_out["top_level_pathway"] = []
            reactome_out["top_level_pathway_genes"] = []
            reactome_out["top_level_pathway_pval_FISH"] = []
            reactome_out["top_level_pathway_pval_BIN"] = []
            reactome_out["top_level_pathway_n"] = []
            reactome_out["top_level_pathway_pct"] = []

            for i in tqdm(set(reactome["top_level_pathway"])):

                query = f'SELECT * FROM REACTOME WHERE "top_level_pathway" IN ("{i}");'

                df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

                res = self.run_enrichment_tests(
                    N=self.occ["Genes_Homo_sapiens"],
                    K=len(set(df["id"])),
                    n=len(set(self.input_data["gene_info"]["sid"])),
                    k=len(set(reactome["id"][reactome["top_level_pathway"] == i])),
                )

                for c in set(
                    reactome["pathway"][reactome["top_level_pathway"].isin([i])]
                ):

                    res2 = self.run_enrichment_tests(
                        N=self.occ["Genes_Homo_sapiens"],
                        K=len(set(df["id"][df["pathway"] == c])),
                        n=len(set(self.input_data["gene_info"]["sid"])),
                        k=len(set(reactome["id"][reactome["pathway"] == c])),
                    )

                    reactome_out["top_level_pathway"].append(i)
                    reactome_out["top_level_pathway_genes"].append(
                        list(
                            set(
                                reactome["found_names"][
                                    reactome["top_level_pathway"] == i
                                ]
                            )
                        )
                    )
                    reactome_out["top_level_pathway_pval_FISH"].append(
                        res["fisher_p_value"]
                    )
                    reactome_out["top_level_pathway_pval_BIN"].append(
                        res["binomial_p_value"]
                    )
                    reactome_out["top_level_pathway_n"].append(
                        len(set(reactome["id"][reactome["top_level_pathway"] == i]))
                    )
                    reactome_out["top_level_pathway_pct"].append(
                        len(set(reactome["id"][reactome["top_level_pathway"] == i]))
                        / len(set(self.input_data["gene_info"]["sid"]))
                    )

                    reactome_out["pathway"].append(c)
                    reactome_out["pathway_genes"].append(
                        list(set(reactome["found_names"][reactome["pathway"] == c]))
                    )
                    reactome_out["complex"].append(
                        list(set(reactome["complex"][reactome["pathway"] == c]))
                    )
                    reactome_out["pathway_pval_FISH"].append(res2["fisher_p_value"])
                    reactome_out["pathway_pval_BIN"].append(res2["binomial_p_value"])
                    reactome_out["pathway_n"].append(
                        len(set(reactome["id"][reactome["pathway"] == c]))
                    )
                    reactome_out["pathway_pct"].append(
                        len(set(reactome["id"][reactome["pathway"] == c]))
                        / len(set(self.input_data["gene_info"]["sid"]))
                    )

            reactome_out = pd.DataFrame(reactome_out)

            # top_level_pathway adjustment
            reactome_out["top_level_pathway_adj_pval_BIN-BF"] = reactome_out[
                "top_level_pathway_pval_BIN"
            ] * len(reactome_out["top_level_pathway_pval_BIN"])
            reactome_out["top_level_pathway_adj_pval_BIN-BF"][
                reactome_out["top_level_pathway_adj_pval_BIN-BF"] >= 1
            ] = 1
            reactome_out["top_level_pathway_adj_pval_FISH-BF"] = reactome_out[
                "top_level_pathway_pval_FISH"
            ] * len(reactome_out["top_level_pathway_pval_FISH"])
            reactome_out["top_level_pathway_adj_pval_FISH-BF"][
                reactome_out["top_level_pathway_adj_pval_FISH-BF"] >= 1
            ] = 1

            reactome_out = reactome_out.sort_values(
                by="top_level_pathway_pval_BIN", ascending=True
            )

            n = len(reactome_out["top_level_pathway_pval_BIN"])

            reactome_out["top_level_pathway_adj_pval_BIN-BH"] = (
                reactome_out["top_level_pathway_pval_BIN"] * n
            ) / np.arange(1, n + 1)

            reactome_out = reactome_out.sort_values(
                by="top_level_pathway_pval_FISH", ascending=True
            )

            reactome_out["top_level_pathway_adj_pval_FISH-BH"] = (
                reactome_out["top_level_pathway_pval_FISH"] * n
            ) / np.arange(1, n + 1)

            reactome_out["top_level_pathway_adj_pval_FISH-BH"][
                reactome_out["top_level_pathway_adj_pval_FISH-BH"] >= 1
            ] = 1
            reactome_out["top_level_pathway_adj_pval_BIN-BH"][
                reactome_out["top_level_pathway_adj_pval_BIN-BH"] >= 1
            ] = 1

            # pathway adjustment
            reactome_out["pathway_adj_pval_BIN-BF"] = reactome_out[
                "pathway_pval_BIN"
            ] * len(reactome_out["pathway_pval_BIN"])
            reactome_out["pathway_adj_pval_BIN-BF"][
                reactome_out["pathway_adj_pval_BIN-BF"] >= 1
            ] = 1
            reactome_out["pathway_adj_pval_FISH-BF"] = reactome_out[
                "pathway_pval_FISH"
            ] * len(reactome_out["pathway_pval_FISH"])
            reactome_out["pathway_adj_pval_FISH-BF"][
                reactome_out["pathway_adj_pval_FISH-BF"] >= 1
            ] = 1

            reactome_out = reactome_out.sort_values(
                by="pathway_pval_BIN", ascending=True
            )

            n = len(reactome_out["pathway_pval_BIN"])

            reactome_out["pathway_adj_pval_BIN-BH"] = (
                reactome_out["pathway_pval_BIN"] * n
            ) / np.arange(1, n + 1)

            reactome_out = reactome_out.sort_values(
                by="pathway_pval_FISH", ascending=True
            )

            reactome_out["pathway_adj_pval_FISH-BH"] = (
                reactome_out["pathway_pval_FISH"] * n
            ) / np.arange(1, n + 1)

            reactome_out["pathway_adj_pval_FISH-BH"][
                reactome_out["pathway_adj_pval_FISH-BH"] >= 1
            ] = 1
            reactome_out["pathway_adj_pval_BIN-BH"][
                reactome_out["pathway_adj_pval_BIN-BH"] >= 1
            ] = 1

            conn.close()

            self.REACTOME_stat = reactome_out.to_dict(orient="list")

        else:
            print(
                "\nREACTOME enrichment analysis could not be performed due to missing REACTOME information in the input data."
            )

    def DISEASES_overrepresentation(self):
        """
        This method conducts an overrepresentation analysis of Human Diseases information.

        Returns:
            Updates `self.DISEASE_stat` with overrepresentation statistics for Human Diseases information.
            To retrieve the results, use the `self.get_DISEASE_statistics` method.
        """

        if "DISEASES" in self.input_data.keys():

            if self.occ is None:
                with open(
                    os.path.join(self.path_in_inside, "occ_dict.json"), "r"
                ) as json_file:
                    self.occ = json.load(json_file)

            diseases_out = {}
            diseases = pd.DataFrame(self.input_data["DISEASES"])

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            diseases_out["disease"] = []
            diseases_out["genes"] = []
            diseases_out["pval_FISH"] = []
            diseases_out["pval_BIN"] = []
            diseases_out["n"] = []
            diseases_out["pct"] = []

            for i in tqdm(set(diseases["disease"])):

                query = f'SELECT * FROM disease WHERE disease IN ("{i}");'

                df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

                res = self.run_enrichment_tests(
                    N=self.occ["Genes_Homo_sapiens"],
                    K=len(set(df["id"][df["disease"] == i])),
                    n=len(set(self.input_data["gene_info"]["sid"])),
                    k=len(set(diseases["id"][diseases["disease"] == i])),
                )

                diseases_out["disease"].append(i)
                diseases_out["genes"].append(
                    list(set(diseases["found_names"][diseases["disease"].isin([i])]))
                )
                diseases_out["pval_FISH"].append(res["fisher_p_value"])
                diseases_out["pval_BIN"].append(res["binomial_p_value"])
                diseases_out["n"].append(
                    len(set(diseases["id"][diseases["disease"] == i]))
                )
                diseases_out["pct"].append(
                    len(set(diseases["id"][diseases["disease"] == i]))
                    / len(set(self.input_data["gene_info"]["sid"]))
                )

            diseases_out = pd.DataFrame(diseases_out)

            diseases_out["adj_pval_BIN-BF"] = diseases_out["pval_BIN"] * len(
                diseases_out["pval_BIN"]
            )
            diseases_out["adj_pval_BIN-BF"][diseases_out["adj_pval_BIN-BF"] >= 1] = 1
            diseases_out["adj_pval_FISH-BF"] = diseases_out["pval_FISH"] * len(
                diseases_out["pval_FISH"]
            )
            diseases_out["adj_pval_FISH-BF"][diseases_out["adj_pval_FISH-BF"] >= 1] = 1

            diseases_out = diseases_out.sort_values(by="pval_BIN", ascending=True)

            n = len(diseases_out["pval_BIN"])

            diseases_out["adj_pval_BIN-BH"] = (
                diseases_out["pval_BIN"] * n
            ) / np.arange(1, n + 1)

            diseases_out = diseases_out.sort_values(by="pval_FISH", ascending=True)

            diseases_out["adj_pval_FISH-BH"] = (
                diseases_out["pval_FISH"] * n
            ) / np.arange(1, n + 1)

            diseases_out["adj_pval_FISH-BH"][diseases_out["adj_pval_FISH-BH"] >= 1] = 1
            diseases_out["adj_pval_BIN-BH"][diseases_out["adj_pval_BIN-BH"] >= 1] = 1

            conn.close()

            self.DISEASE_stat = diseases_out.to_dict(orient="list")

        else:
            print(
                "\nDISEASES enrichment analysis could not be performed due to missing DISEASES information in the input data."
            )

    def ViMIC_overrepresentation(self):
        """
        This method conducts an overrepresentation analysis of viral diseases ViMIC information.

        Returns:
            Updates `self.ViMIC_stat` with overrepresentation statistics for ViMIC information.
            To retrieve the results, use the `self.get_ViMIC_statistics` method.
        """

        if "ViMIC" in self.input_data.keys():

            if self.occ is None:
                with open(
                    os.path.join(self.path_in_inside, "occ_dict.json"), "r"
                ) as json_file:
                    self.occ = json.load(json_file)

            vimic_out = {}
            vimic = pd.DataFrame(self.input_data["ViMIC"])

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            vimic_out["virus"] = []
            vimic_out["genes"] = []
            vimic_out["group"] = []

            vimic_out["pval_FISH"] = []
            vimic_out["pval_BIN"] = []
            vimic_out["n"] = []
            vimic_out["pct"] = []

            for i in tqdm(set(vimic["virus"])):

                query = f'SELECT * FROM ViMIC WHERE virus IN ("{i}");'

                df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

                res = self.run_enrichment_tests(
                    N=self.occ["Genes_Homo_sapiens"],
                    K=len(set(df["id"][df["virus"] == i])),
                    n=len(set(self.input_data["gene_info"]["sid"])),
                    k=len(set(vimic["id"][vimic["virus"] == i])),
                )

                vimic_out["virus"].append(i)
                vimic_out["genes"].append(
                    list(set(vimic["found_names"][vimic["virus"].isin([i])]))
                )
                vimic_out["group"].append(
                    list(set(vimic["group"][vimic["virus"].isin([i])]))
                )
                vimic_out["pval_FISH"].append(res["fisher_p_value"])
                vimic_out["pval_BIN"].append(res["binomial_p_value"])
                vimic_out["n"].append(len(set(vimic["id"][vimic["virus"] == i])))
                vimic_out["pct"].append(
                    len(set(vimic["id"][vimic["virus"] == i]))
                    / len(set(self.input_data["gene_info"]["sid"]))
                )

            vimic_out = pd.DataFrame(vimic_out)

            vimic_out["adj_pval_BIN-BF"] = vimic_out["pval_BIN"] * len(
                vimic_out["pval_BIN"]
            )
            vimic_out["adj_pval_BIN-BF"][vimic_out["adj_pval_BIN-BF"] >= 1] = 1
            vimic_out["adj_pval_FISH-BF"] = vimic_out["pval_FISH"] * len(
                vimic_out["pval_FISH"]
            )
            vimic_out["adj_pval_FISH-BF"][vimic_out["adj_pval_FISH-BF"] >= 1] = 1

            vimic_out = vimic_out.sort_values(by="pval_BIN", ascending=True)

            n = len(vimic_out["pval_BIN"])

            vimic_out["adj_pval_BIN-BH"] = (vimic_out["pval_BIN"] * n) / np.arange(
                1, n + 1
            )

            vimic_out = vimic_out.sort_values(by="pval_FISH", ascending=True)

            vimic_out["adj_pval_FISH-BH"] = (vimic_out["pval_FISH"] * n) / np.arange(
                1, n + 1
            )

            vimic_out["adj_pval_FISH-BH"][vimic_out["adj_pval_FISH-BH"] >= 1] = 1
            vimic_out["adj_pval_BIN-BH"][vimic_out["adj_pval_BIN-BH"] >= 1] = 1

            conn.close()

            self.ViMIC_stat = vimic_out.to_dict(orient="list")

        else:
            print(
                "\nViMIC enrichment analysis could not be performed due to missing ViMIC information in the input data."
            )

    def features_specificity(self):
        """
        This method conducts an overrepresentation analysis of tissue specificity on Human Protein Atlas (HPA) information.

        Returns:
            Updates `self.specificity_stat` with overrepresentation statistics for specificity information.
            To retrieve the results, use the `self.get_specificity_statistics` method.
        """

        if "HPA" in self.input_data.keys():

            if self.occ is None:
                with open(
                    os.path.join(self.path_in_inside, "occ_dict.json"), "r"
                ) as json_file:
                    self.occ = json.load(json_file)

            HPA_out = {}

            HPA = self.input_data["HPA"]

            conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

            for k in HPA.keys():
                if k != "HPA_blood_markers":
                    tmp = pd.DataFrame(HPA[k])

                    tmp_out = {}

                    tmp_out["specificity"] = []
                    tmp_out["genes"] = []
                    tmp_out["pval_FISH"] = []
                    tmp_out["pval_BIN"] = []
                    tmp_out["n"] = []
                    tmp_out["pct"] = []

                    col_name = None

                    if "location" in list(tmp.columns):
                        col_name = "location"
                    else:
                        col_name = "name"

                    for i in tqdm(set(tmp[col_name])):

                        query = f'SELECT * FROM {k} WHERE {col_name} IN ("{i}");'

                        df = pd.read_sql_query(query, conn).applymap(
                            self.deserialize_data
                        )

                        res = self.run_enrichment_tests(
                            N=self.occ["Genes_Homo_sapiens"],
                            K=len(set(df["id"][df[col_name] == i])),
                            n=len(set(self.input_data["gene_info"]["sid"])),
                            k=len(set(tmp["id"][tmp[col_name] == i])),
                        )

                        tmp_out["specificity"].append(i)
                        tmp_out["genes"].append(
                            list(set(tmp["found_names"][tmp[col_name].isin([i])]))
                        )
                        tmp_out["pval_FISH"].append(res["fisher_p_value"])
                        tmp_out["pval_BIN"].append(res["binomial_p_value"])
                        tmp_out["n"].append(len(set(tmp["id"][tmp[col_name] == i])))
                        tmp_out["pct"].append(
                            len(set(tmp["id"][tmp[col_name] == i]))
                            / len(set(self.input_data["gene_info"]["sid"]))
                        )

                    tmp_out = pd.DataFrame(tmp_out)

                    tmp_out["adj_pval_BIN-BF"] = tmp_out["pval_BIN"] * len(
                        tmp_out["pval_BIN"]
                    )
                    tmp_out["adj_pval_BIN-BF"][tmp_out["adj_pval_BIN-BF"] >= 1] = 1
                    tmp_out["adj_pval_FISH-BF"] = tmp_out["pval_FISH"] * len(
                        tmp_out["pval_FISH"]
                    )
                    tmp_out["adj_pval_FISH-BF"][tmp_out["adj_pval_FISH-BF"] >= 1] = 1

                    tmp_out = tmp_out.sort_values(by="pval_BIN", ascending=True)

                    n = len(tmp_out["pval_BIN"])

                    tmp_out["adj_pval_BIN-BH"] = (tmp_out["pval_BIN"] * n) / np.arange(
                        1, n + 1
                    )

                    tmp_out = tmp_out.sort_values(by="pval_FISH", ascending=True)

                    tmp_out["adj_pval_FISH-BH"] = (
                        tmp_out["pval_FISH"] * n
                    ) / np.arange(1, n + 1)

                    tmp_out["adj_pval_FISH-BH"][tmp_out["adj_pval_FISH-BH"] >= 1] = 1
                    tmp_out["adj_pval_BIN-BH"][tmp_out["adj_pval_BIN-BH"] >= 1] = 1

                    HPA_out[k] = tmp_out.to_dict(orient="list")

            conn.close()

            self.specificity_stat = HPA_out

        else:
            print(
                "\nHPA enrichment analysis could not be performed due to missing HPA information in the input data."
            )

    def gene_interaction(self):
        """
        This method conducts an Genes Interaction (GI) analysis of STRING / IntAct information.

        Returns:
            Updates `self.features_interactions` with overrepresentation statistics for GI information.
            To retrieve the results, use the `self.get_features_interactions_statistics` method.
        """

        interaction_mapping = {
            "coexpression": ["gene -> gene"],
            "coexpression_transferred": ["gene -> gene"],
            "cooccurence": ["gene -> gene"],
            "database": ["protein -> protein"],
            "database_transferred": ["protein -> protein"],
            "experiments": ["protein -> protein"],
            "experiments_transferred": ["protein -> protein"],
            "fusion": ["gene -> gene"],
            "homology": ["protein -> protein"],
            "neighborhood": ["gene -> gene"],
            "neighborhood_transferred": ["gene -> gene"],
            "textmining": ["protein -> protein"],
            "textmining_transferred": ["protein -> protein"],
        }

        interactome = {}

        if "IntAct" in self.input_data.keys() and "STRING" in self.input_data.keys():

            ia = pd.DataFrame(self.input_data["IntAct"]["gene_products"])
            ia = ia[ia["source"].isin(self.interaction_source)]
            ia = ia[ia["species"].isin(self.species_study)]

            interactome["A"] = list(ia["found_names_1"])
            interactome["B"] = list(ia["found_names_2"])
            interactome["interaction_type"] = list(ia["interaction_type"])
            interactome["connection_type"] = [
                f"{a} -> {b}"
                for a, b in zip(ia["interactor_type_1"], ia["interactor_type_2"])
            ]
            interactome["source"] = list(ia["source"])

            ia = pd.DataFrame(self.input_data["STRING"])
            ia = ia[ia["species"].isin(self.species_study)]
            ia = ia[ia["combined_score"] >= self.interaction_strength]

            interactome["A"] = list(interactome["A"]) + list(ia["found_names_1"])
            interactome["B"] = list(interactome["B"]) + list(ia["found_names_2"])
            interactome["source"] = list(interactome["source"]) + ["STRING"] * len(
                list(ia["source"])
            )
            interactome["interaction_type"] = list(interactome["interaction_type"]) + [
                None
            ] * len(list(ia["source"]))
            interactome["connection_type"] = list(interactome["connection_type"]) + [
                self.map_interactions_flat(x, interaction_mapping) for x in ia["source"]
            ]

            interactome = pd.DataFrame(interactome)
            interactome = interactome[
                interactome["source"].isin(self.interaction_source)
            ]
            interactome = interactome.explode("connection_type")
            interactome = interactome.to_dict(orient="list")

            self.features_interactions = interactome

        elif "IntAct" in self.input_data.keys():

            ia = pd.DataFrame(self.input_data["IntAct"]["gene_products"])
            ia = ia[ia["source"].isin(self.interaction_source)]
            ia = ia[ia["species"].isin(self.species_study)]

            interactome["A"] = list(ia["found_names_1"])
            interactome["B"] = list(ia["found_names_2"])
            interactome["interaction_type"] = list(ia["interaction_type"])
            interactome["connection_type"] = [
                f"{a} -> {b}"
                for a, b in zip(ia["interactor_type_1"], ia["interactor_type_2"])
            ]
            interactome["source"] = list(ia["source"])

            self.features_interactions = interactome

        elif "STRING" in self.input_data.keys():

            ia = pd.DataFrame(self.input_data["STRING"])
            ia = ia[ia["species"].isin(self.species_study)]
            ia = ia[ia["combined_score"] >= self.interaction_strength]

            interactome["A"] = list(ia["found_names_1"])
            interactome["B"] = list(ia["found_names_2"])
            interactome["source"] = ["STRING"] * len(list(ia["source"]))
            interactome["interaction_type"] = [None] * len(list(ia["source"]))
            interactome["connection_type"] = [
                self.map_interactions_flat(x, interaction_mapping) for x in ia["source"]
            ]

            interactome = pd.DataFrame(interactome)
            interactome = interactome[
                interactome["source"].isin(self.interaction_source)
            ]
            interactome = interactome.explode("connection_type")
            interactome = interactome.to_dict(orient="list")

            self.features_interactions = interactome

        else:
            print(
                "\nGene interaction analysis could not be performed due to missing STRING/IntAct information in the input data."
            )

    def GO_network(self):
        """
        This method conducts an network analysis of GO-TERM data.

        Returns:
            Updates `self.GO_net` with GO-TERM network data.
            To retrieve the results, use the `self.get_GO_network` method.
        """

        if "GO-TERM" in self.input_data.keys():

            goh = pd.DataFrame(self.input_data["GO-TERM"]["hierarchy"])

            relation_colors = {
                "is_a_ids": "blue",
                "part_of_ids": "orange",
                "has_part_ids": "green",
                "regulates_ids": "red",
                "negatively_regulates_ids": "purple",
                "positively_regulates_ids": "brown",
            }

            df_list = []

            for i in [
                "is_a_ids",
                "part_of_ids",
                "has_part_ids",
                "regulates_ids",
                "negatively_regulates_ids",
                "positively_regulates_ids",
            ]:
                tmp = goh[[i, "GO_id"]]
                tmp = tmp[tmp[i].notna()]
                tmp.columns = ["parent", "children"]
                tmp["color"] = relation_colors[i]
                if len(tmp.index) > 0:
                    df_list.append(tmp)

            full_df = pd.concat(df_list, ignore_index=True)

            del df_list

            goh = pd.DataFrame(self.input_data["GO-TERM"]["gene_info"])

            found_name_map = dict(zip(goh["GO_id"], goh["found_names"]))

            full_df["found_names_x"] = full_df["parent"].map(found_name_map)

            full_df["found_names_y"] = full_df["children"].map(found_name_map)

            full_df["features"] = full_df["found_names_x"].combine(
                full_df["found_names_y"], lambda a, b: list({a, b})
            )

            # sprzątanie
            full_df.drop(columns=["found_names_x", "found_names_y"], inplace=True)

            del goh

            full_df = full_df.explode("features")

            go_out = pd.DataFrame(self.GO_stat)

            test_col = self.select_test(
                self.network_stat["test"], self.network_stat["adj"]
            )

            if self.network_stat["parent_stat"]:
                go_out_parent = go_out[
                    go_out[f"parent_{test_col}"] <= self.network_stat["p_val"]
                ]
            else:
                go_out_parent = go_out

            go_out_children = go_out[
                go_out[f"child_{test_col}"] <= self.network_stat["p_val"]
            ]

            full_list = list(set(go_out_parent["parent"])) + list(
                set(go_out_children["child"])
            )

            full_df = full_df[full_df["parent"].isin(full_list)]
            full_df = full_df[full_df["children"].isin(full_list)]

            gn = pd.DataFrame(self.input_data["GO-TERM"]["go_names"])

            name_mapping = dict(zip(gn["GO_id"], gn["name"]))
            full_df["parent"] = full_df["parent"].map(name_mapping)
            full_df["children"] = full_df["children"].map(name_mapping)

            self.GO_net = full_df.to_dict(orient="list")

        else:
            print("\nMissing GO information in the input data.")

    def KEGG_network(self):
        """
        This method conducts an network analysis of KEGG data.

        Returns:
            Updates `self.KEGG_net` with Reactome network data.
            To retrieve the results, use the `self.get_KEGG_network` method.
        """

        if "KEGG" in self.input_data.keys():

            kegg = pd.DataFrame(self.input_data["KEGG"])

            full_df = pd.DataFrame()

            full_df["parent"] = kegg["2nd"]
            full_df["children"] = kegg["3rd"]
            full_df["features"] = kegg["found_names"]

            kegg_out = pd.DataFrame(self.KEGG_stat)

            test_col = self.select_test(
                self.network_stat["test"], self.network_stat["adj"]
            )

            kegg_out = kegg_out[
                kegg_out[f"3rd_{test_col}"] <= self.network_stat["p_val"]
            ]

            if self.network_stat["parent_stat"]:
                kegg_out = kegg_out[
                    kegg_out[f"2nd_{test_col}"] <= self.network_stat["p_val"]
                ]

            full_df = full_df[full_df["parent"].isin(kegg_out["2nd"])]
            full_df = full_df[full_df["children"].isin(kegg_out["3rd"])]

            full_df["color"] = "gold"

            self.KEGG_net = full_df.to_dict(orient="list")

        else:
            print("\nMissing KEGG information in the input data.")

    def REACTOME_network(self):
        """
        This method conducts an network analysis of Reactome data.

        Returns:
            Updates `self.REACTOME_net` with Reactome network data.
            To retrieve the results, use the `self.get_REACTOME_network` method.
        """

        if "REACTOME" in self.input_data.keys():

            reactome = pd.DataFrame(self.input_data["REACTOME"])

            full_df = pd.DataFrame()

            full_df["parent"] = reactome["top_level_pathway"]
            full_df["children"] = reactome["pathway"]
            full_df["features"] = reactome["found_names"]

            reactome_out = pd.DataFrame(self.REACTOME_stat)

            test_col = self.select_test(
                self.network_stat["test"], self.network_stat["adj"]
            )

            if self.network_stat["parent_stat"]:
                reactome_out = reactome_out[
                    reactome_out[f"top_level_pathway_{test_col}"]
                    <= self.network_stat["p_val"]
                ]

            reactome_out = reactome_out[
                reactome_out[f"pathway_{test_col}"] <= self.network_stat["p_val"]
            ]

            full_df = full_df[full_df["parent"].isin(reactome_out["top_level_pathway"])]
            full_df = full_df[full_df["children"].isin(reactome_out["pathway"])]

            full_df["color"] = "silver"

            self.REACTOME_net = full_df.to_dict(orient="list")

        else:
            print("\nMissing REACTOME information in the input data.")

    def full_analysis(self):
        """
        This method conducts a full analysis of `Enrichment` class results obtained using the `self.get_results` method:

            * statistics:
                - Human Protein Atlas (HPA) [see self.features_specificity() method]
                - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see self.KEGG_overrepresentation() method]
                - GeneOntology (GO-TERM) [see self.GO_overrepresentation() method]
                - Reactome [see self.REACTOME_overrepresentation() method]
                - Human Diseases [see self.DISEASES_overrepresentation() method]
                - Viral Diseases (ViMIC) [see self.ViMIC_overrepresentation() method]
             * networks:
                 - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see self.KEGG_network() method]
                 - GeneOntology (GO-TERM) [see self.GO_network() method]
                 - Reactome [see self.REACTOME_network() method]


        Returns:
            To retrieve the results, use the `self.get_full_results` method.
        """

        print("\nGO-TERM overrepresentation analysis...")
        self.GO_overrepresentation()

        print("\nKEGG overrepresentation analysis...")
        self.KEGG_overrepresentation()

        print("\nREACTOME overrepresentation analysis...")
        self.REACTOME_overrepresentation()

        print("\nViMIC overrepresentation analysis...")
        self.ViMIC_overrepresentation()

        print("\nDISEASES overrepresentation analysis...")
        self.DISEASES_overrepresentation()

        print("\nSpecificity overrepresentation analysis...")
        self.features_specificity()

        print("\nInteraction analysis...")
        self.gene_interaction()

        print("\nNetwork creating...")
        self.REACTOME_network()
        self.KEGG_network()
        self.GO_network()

        print("\nComplete!")

    def get_full_results(self):
        """
        This method returns the full analysis dictionary containing on keys:
            * 'enrichment':
                - 'gene_info' - genome information for the selected gene set [see `self.get_gene_info`]
                - 'HPA' - Human Protein Atlas (HPA) [see 'self.get_HPA']
                - 'KEGG' - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see 'self.get_KEGG']
                - 'GO-TERM' - GeneOntology (GO-TERM) [see 'self.get_GO_TERM']
                - 'REACTOME' - Reactome [see 'self.get_REACTOME']
                - 'DISEASES' - Human Diseases [see 'self.get_DISEASES']
                - 'ViMIC' - Viral Diseases (ViMIC) [see 'self.get_ViMIC']
                - 'IntAct' - IntAct [see 'self.get_IntAct']
                - 'STRING' - STRING [see 'self.get_STRING']
                - 'CellConnections' - CellConnections (CellPhone / CellTalk) [see 'self.get_CellCon']
                - 'RNA-SEQ' - RNAseq data specific to tissues [see 'self.get_RNA_SEQ']

             * 'statistics':
                 - 'specificity' - Human Protein Atlas (HPA) [see 'self.get_specificity_statistics']
                 - 'KEGG' - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see 'self.get_KEGG_statistics']
                 - 'GO-TERM' - GeneOntology (GO-TERM) [see 'self.get_GO_statistics']
                 - 'REACTOME' - Reactome [see 'self.get_REACTOME_statistics']
                 - 'DISEASES' - Human Diseases [see 'self.get_DISEASE_statistics']
                 - 'ViMIC' - Viral Diseases (ViMIC) [see 'self.get_ViMIC_statistics']
                 - 'interactions' - STRING / IntAct [see 'self.get_features_interactions_statistics']

             * 'networks':
                 - 'KEGG' - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see 'self.get_KEGG_network']
                 - 'GO-TERM' - GeneOntology (GO-TERM) [see 'self.get_GO_network']
                 - 'REACTOME' - Reactome [see 'self.get_REACTOME_network']

        Returns:
            dict (dict) - full analysis data
        """

        full_results = {}

        full_results["enrichment"] = self.input_data

        stats = {}
        networks = {}

        try:
            stats["KEGG"] = self.get_KEGG_statistics()
        except:
            pass

        try:
            stats["REACTOME"] = self.get_REACTOME_statistics()
        except:
            pass

        try:
            stats["GO-TERM"] = self.get_GO_statistics()
        except:
            pass

        try:
            stats["ViMIC"] = self.get_ViMIC_statistics()
        except:
            pass

        try:
            stats["DISEASES"] = self.get_DISEASE_statistics()
        except:
            pass

        try:
            stats["specificity"] = self.get_specificity_statistics()
        except:
            pass

        try:
            stats["interactions"] = self.get_features_interactions_statistics()
        except:
            pass

        try:
            networks["KEGG"] = self.get_KEGG_network()
        except:
            pass

        try:
            networks["REACTOME"] = self.get_REACTOME_network()
        except:
            pass

        try:
            networks["GO-TERM"] = self.get_GO_network()
        except:
            pass

        full_results["statistics"] = stats

        full_results["statistics"]["setup"] = {}

        full_results["statistics"]["setup"]["network_stat"] = self.network_stat

        full_results["statistics"]["setup"]["go_grade"] = self.go_grade

        full_results["statistics"]["setup"][
            "interaction_strength"
        ] = self.interaction_strength

        full_results["statistics"]["setup"][
            "interaction_source"
        ] = self.interaction_source

        full_results["networks"] = networks

        return full_results


class Visualization:
    """
    The `Visualization` class provides tools for statistical and network analysis of `Analysis` class results obtained using the `self.get_full_results` method.

    Args:
        input_data (dict) - output data from the `Analysis` class `self.get_full_results` method

    """

    def __init__(self, input_data: dict):

        self.input_data = input_data
        self.show_plot = False
        self.parent_stats = False

        super().__init__()

    def set_parent_stats(self, stats):
        """
        This method sets the parent statistical test value used for graph creation.

            Avaiable values:
                - True - use test p-value for drop non-significient parents
                - False - not use test p-value for drop non-significient parents

            Args:
                test (bool) - bool value [True/False]
        """

        if stats in [True, False]:
            self.parent_stats = stats

        else:

            raise ValueError("\nStats should be included in True or False")

    def select_test(self, test, adj):
        try:
            test_string = ""

            if adj != None and adj.upper() in ["BF", "BH"]:
                test_string = test_string + "adj_pval_"
            else:
                test_string = test_string + "pval_"

            if test != None and test.upper() == "BIN":
                test_string = test_string + "BIN"
            elif test != None and test.upper() == "FISH":
                test_string = test_string + "FISH"
            else:
                test_string = test_string + "BIN"

            if adj != None and adj.upper() == "BF":
                test_string = test_string + "-BF"
            elif adj != None and adj.upper() == "BH":
                test_string = test_string + "-BH"
            else:
                test_string = test_string + ""

            return test_string
        except:
            print("\n")
            print("Provided wrong test input!")

    def bar_plot(
        self,
        data,
        n=25,
        side="right",
        color="blue",
        width=10,
        bar_width=0.5,
        stat="p_val",
        sets="GO-TERM",
        column="name",
        x_max=None,
        show_axis=True,
        title=None,
        ax=None,
    ):

        tmp = pd.DataFrame(data)

        if stat.upper() == "perc".upper():
            tmp = (
                tmp.sort_values(by="n", ascending=False)
                .reset_index(drop=True)
                .iloc[0:n, :]
            )
            x_label = "Percent of genes [%]"
            values = tmp["pct"]
        elif stat.upper() == "p_val".upper():
            tmp = (
                tmp.sort_values(by="-log(p-val)", ascending=False)
                .reset_index(drop=True)
                .iloc[0:n, :]
            )
            x_label = "-log(p-val)"
            values = tmp["-log(p-val)"]
        else:
            tmp = (
                tmp.sort_values(by="n", ascending=False)
                .reset_index(drop=True)
                .iloc[0:n, :]
            )
            x_label = "Number of genes"
            values = tmp["n"]

        if ax is None:
            fig_1, ax = plt.subplots(figsize=(width, float(len(tmp[column]) / 2.5)))

        ax.barh(tmp[column], values, color=color, height=bar_width)

        if show_axis:
            ax.set_xlabel(x_label)
        else:
            ax.spines["bottom"].set_visible(False)
            ax.tick_params(
                axis="x", which="both", bottom=False, top=False, labelbottom=False
            )

        ax.set_ylabel("")
        ax.invert_yaxis()

        if title:
            ax.set_title(title)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

        if x_max is not None:
            ax.set_xlim(0, x_max)

        if side == "right":
            ax.yaxis.tick_right()
        elif side == "left":
            ax.invert_xaxis()

        if ax is None:
            if self.show_plot:
                plt.show()
            elif self.show_plot is False:
                plt.close(fig_1)

        try:
            return fig_1
        except:
            return ax

    def bar_plot_blood(
        self,
        data,
        n=25,
        side="right",
        color="red",
        width=10,
        bar_width=0.5,
        stat=None,
        sets=None,
        column=None,
        x_max=None,
        show_axis=True,
        title=None,
        ax=None,
    ):

        tmp = pd.DataFrame(data)

        tmp = (
            tmp.sort_values(by=stat, ascending=False)
            .reset_index(drop=True)
            .iloc[0:n, :]
        )
        x_label = stat
        values = tmp[stat]

        if ax is None:
            fig_1, ax = plt.subplots(figsize=(width, float(len(tmp[column]) / 2.5)))

        ax.barh(tmp[column], values, color=color, height=bar_width)

        if show_axis:
            ax.set_xlabel(x_label)
        else:
            ax.spines["bottom"].set_visible(False)
            ax.tick_params(
                axis="x", which="both", bottom=False, top=False, labelbottom=False
            )

        ax.set_ylabel("")
        ax.invert_yaxis()

        if title:
            ax.set_title(title)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

        if x_max is not None:
            ax.set_xlim(0, x_max)

        if side == "right":
            ax.yaxis.tick_right()
        elif side == "left":
            ax.invert_xaxis()

        if ax is None:

            if self.show_plot:
                plt.show()
            elif self.show_plot is False:
                plt.close(fig_1)

        try:
            return fig_1
        except:
            return ax

    def gene_type_plot(self, cmap="summer", image_width=6, image_high=6, font_size=15):
        """
        This method generates a pie chart visualizing the distribution of gene types based on enrichment data.

        Args:
            cmap (str) - colormap used for the pie chart. Default is 'summer'
            image_width (int) - width of the plot in inches. Default is 6
            image_high (int) - height of the plot in inches. Default is 6
            font_size (int) - font size. Default is 15

        Returns:
            fig (matplotlib.figure.Figure) - figure object containing a pie chart that visualizes the distribution of gene type occurrences as percentages
        """

        tmp_info = self.input_data["enrichment"]["gene_info"]

        sp = self.input_data["enrichment"]["species"]["species_genes"]

        h_genes = []
        m_genes = []
        r_genes = []

        if "Homo sapiens" in sp:

            h_genes = tmp_info["gen_type_Homo_sapiens"]

        if "Mus musculus" in sp:

            m_genes = tmp_info["gen_type_Mus_musculus"]

        if "Rattus norvegicus" in sp:

            r_genes = tmp_info["gen_type_Rattus_norvegicus"]

        full_genes = []
        for i in range(len(tmp_info["sid"])):
            g = []

            if len(h_genes) > 0:
                if isinstance(h_genes[i], list):
                    g += h_genes[i]
                elif h_genes[i] is None:
                    g += []
                else:
                    g.append(h_genes[i])

            if len(m_genes) > 0:
                if isinstance(m_genes[i], list):
                    g += m_genes[i]
                elif m_genes[i] is None:
                    g += []
                else:
                    g.append(m_genes[i])

            if len(r_genes) > 0:
                if isinstance(r_genes[i], list):
                    g += r_genes[i]
                elif r_genes[i] is None:
                    g += []
                else:
                    g.append(r_genes[i])

            if len(g) == 0:
                g = ["undefined"]

            full_genes += list(set(g))

        count_gene = Counter(full_genes)

        count_gene = pd.DataFrame(count_gene.items(), columns=["gene_type", "n"])

        count_gene["pct"] = (count_gene["n"] / sum(count_gene["n"])) * 100

        count_gene["pct"] = [round(x, 2) for x in count_gene["pct"]]

        count_gene = count_gene.sort_values("n", ascending=False)

        count_gene = count_gene.reset_index(drop=True)

        labels = (
            count_gene["gene_type"]
            + [" : "] * len(count_gene["gene_type"])
            + count_gene["pct"].astype(str)
            + ["%"] * len(count_gene["gene_type"])
        )

        cn = len(count_gene["gene_type"])

        existing_cmap = plt.get_cmap(cmap)

        colors = [existing_cmap(i / cn) for i in range(cn)]

        colordf = pd.DataFrame({"color": colors, "label": labels})

        fig, ax = plt.subplots(
            figsize=(image_width, image_high), subplot_kw=dict(aspect="equal")
        )

        wedges, texts = ax.pie(
            count_gene["pct"],
            startangle=90,
            labeldistance=1.05,
            colors=[
                colordf["color"][colordf["label"] == x][
                    colordf.index[colordf["label"] == x][0]
                ]
                for x in labels
            ],
            wedgeprops={"linewidth": 0.5, "edgecolor": "black"},
        )

        kw = dict(arrowprops=dict(arrowstyle="-"), zorder=0, va="center")
        n = 0
        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            if len(labels[i]) > 0:
                n += 0.45
                ax.annotate(
                    labels[i],
                    xy=(x, y),
                    xytext=(1.4 * x + (n * x / 4), y * 1.1 + (n * y / 4)),
                    horizontalalignment=horizontalalignment,
                    fontsize=font_size,
                    weight="bold",
                    **kw,
                )

        circle2 = plt.Circle((0, 0), 0.6, color="white")
        circle2.set_edgecolor("black")

        ax.text(
            0.5,
            0.5,
            "Gene type",
            transform=ax.transAxes,
            va="center",
            ha="center",
            backgroundcolor="white",
            weight="bold",
            fontsize=int(font_size * 1.25),
        )

        p = plt.gcf()
        p.gca().add_artist(circle2)

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def GO_plot(
        self,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n=10,
        min_terms: int = 5,
        selected_parent: list = [],
        side="right",
        color="blue",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):
        """
        This method generates a bar plot for Gene Ontology (GO) term enrichment and statistical analysis.

        Args:
            p_val (float) - significance threshold for p-values. Default is 0.05
            test (str) - statistical test to use ('FISH' - Fisher's Exact Test or 'BIN' - binomial test). Default is 'FISH'
            adj (str) - method for p-value adjustment ('BH' - Benjamini-Hochberg, 'BF' - Benjamini-Hochberg). Default is 'BH'
            n (int) - maximum number of terms to display per category. Default is 10
            min_terms (int) - minimum number of child terms required for a parent term to be included. Default is 5
            selected_parent (list) - list of specific parent terms to include in the plot. If empty, all parent terms are included. Default is []
            side (str) - side on which the bars are displayed ('left' or 'right'). Default is 'right'
            color (str) - color of the bars in the plot. Default is 'blue'
            width (int) - width of the plot in inches. Default is 10
            bar_width (float / int) - width of individual bars. Default is 0.5
            stat (str) - statistic to use for the x-axis ('p_val', 'n', or 'perc'). Default is 'p_val'

        Returns:
            fig (matplotlib.figure.Figure) - matplotlib Figure object containing the bar plots
        """

        sets = "GO-TERM"
        column = "child_name"

        test_string = self.select_test(test, adj)

        tmp_in = pd.DataFrame(self.input_data["statistics"][sets])
        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"parent_{test_string}"] <= p_val]
        tmp_in = tmp_in[tmp_in[f"child_{test_string}"] <= p_val]
        tmp_in[f"child_{test_string}"] = (
            tmp_in[f"child_{test_string}"]
            + np.min(
                tmp_in[f"child_{test_string}"][tmp_in[f"child_{test_string}"] != 0]
            )
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"child_{test_string}"])
        tmp_in = tmp_in.reset_index(drop=True)

        if stat.upper() == "perc".upper():
            x_max = np.max(tmp_in["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(tmp_in["-log(p-val)"])

        else:
            x_max = np.max(tmp_in["n"])

        iter_set = list(set(tmp_in["parent_name"]))

        if len(selected_parent) > 0:
            tmp_iter = []
            for i in selected_parent:
                if i in iter_set:
                    tmp_iter.append(i)
                else:
                    print(f"\nParent term name: {i} was not found")

            iter_set = tmp_iter

            if len(iter_set) == 0:
                raise ValueError("Nothing to return")

        hlist = []

        valid_iter_set = []

        for l, it in enumerate(iter_set):

            inx = [x for x in tmp_in.index if it in tmp_in["parent_name"][x]]
            tmp = tmp_in.loc[inx]

            if len(set(tmp[column])) >= min_terms:
                valid_iter_set.append(it)

                if float(len(set(tmp[column]))) > n:

                    tn = n
                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / 2.1)

                else:

                    tn = float(len(set(tmp[column])))

                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))

                    else:
                        hlist.append(tn / 2.1)

        iter_set = valid_iter_set

        fig = plt.figure(figsize=(width, sum(hlist)))

        gs = GridSpec(len(hlist), 1, height_ratios=hlist)

        gs.update(hspace=len(hlist) / 50)

        for l, i in enumerate(iter_set):
            inx = [x for x in tmp_in.index if i in tmp_in["parent_name"][x]]
            tmp = tmp_in.loc[inx]

            ax = fig.add_subplot(gs[l])

            show_axis = l + 1 == len(iter_set)

            self.bar_plot(
                data=tmp,
                n=n,
                side=side,
                color="blue",
                width=width,
                bar_width=bar_width,
                stat=stat,
                sets="GO-TERM",
                column=column,
                x_max=x_max,
                show_axis=show_axis,
                title=i,
                ax=ax,
            )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def KEGG_plot(
        self,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n=10,
        min_terms: int = 5,
        selected_parent: list = [],
        side="right",
        color="orange",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):
        """
        This method generates a bar plot for KEGG term enrichment and statistical analysis.

        Args:
            p_val (float) - significance threshold for p-values. Default is 0.05
            test (str) - statistical test to use ('FISH' - Fisher's Exact Test or 'BIN' - binomial test). Default is 'FISH'
            adj (str) - method for p-value adjustment ('BH' - Benjamini-Hochberg, 'BF' - Benjamini-Hochberg). Default is 'BH'
            n (int) - maximum number of terms to display per category. Default is 10
            min_terms (int) - minimum number of child terms required for a parent term to be included. Default is 5
            selected_parent (list) - list of specific parent terms to include in the plot. If empty, all parent terms are included. Default is []
            side (str) - side on which the bars are displayed ('left' or 'right'). Default is 'right'
            color (str) - color of the bars in the plot. Default is 'orange'
            width (int) - width of the plot in inches. Default is 10
            bar_width (float / int) - width of individual bars. Default is 0.5
            stat (str) - statistic to use for the x-axis ('p_val', 'n', or 'perc'). Default is 'p_val'

        Returns:
            fig (matplotlib.figure.Figure) - matplotlib Figure object containing the bar plots
        """

        sets = "KEGG"
        column = "3rd"

        test_string = self.select_test(test, adj)

        tmp_in = pd.DataFrame(self.input_data["statistics"][sets])
        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"2nd_{test_string}"] <= p_val]
        tmp_in = tmp_in[tmp_in[f"3rd_{test_string}"] <= p_val]
        tmp_in[f"3rd_{test_string}"] = (
            tmp_in[f"3rd_{test_string}"]
            + np.min(tmp_in[f"3rd_{test_string}"][tmp_in[f"3rd_{test_string}"] != 0])
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"3rd_{test_string}"])
        tmp_in = tmp_in.reset_index(drop=True)

        if stat.upper() == "perc".upper():
            x_max = np.max(tmp_in["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(tmp_in["-log(p-val)"])

        else:
            x_max = np.max(tmp_in["n"])

        # queue

        tmp_qq = tmp_in[["2nd", "-log(p-val)"]]

        tmp_qq["amount"] = tmp_qq["2nd"].map(tmp_qq["2nd"].value_counts())

        tmp_qq = tmp_qq.groupby("2nd", as_index=False).agg(
            amount=("amount", "first"), avg_log_pval=("-log(p-val)", "mean")
        )

        tmp_qq = tmp_qq.sort_values(
            by=["amount", "avg_log_pval"], ascending=[False, False]
        ).reset_index(drop=True)

        #######################################################################
        iter_set = list(tmp_qq["2nd"])

        hlist = []

        valid_iter_set = []

        for l, it in enumerate(iter_set):

            inx = [x for x in tmp_in.index if it in tmp_in["2nd"][x]]
            tmp = tmp_in.loc[inx]

            if len(set(tmp[column])) >= min_terms:
                valid_iter_set.append(it)

                if float(len(set(tmp[column]))) > n:

                    tn = n
                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / 2.1)

                else:

                    tn = float(len(set(tmp[column])))

                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))

                    else:
                        hlist.append(tn / 2.1)

        iter_set = valid_iter_set

        fig = plt.figure(figsize=(width, sum(hlist)))

        gs = GridSpec(len(hlist), 1, height_ratios=hlist)
        gs.update(hspace=len(hlist) / 50)

        for l, i in enumerate(iter_set):
            inx = [x for x in tmp_in.index if i in tmp_in["2nd"][x]]
            tmp = tmp_in.loc[inx]

            ax = fig.add_subplot(gs[l])

            show_axis = l + 1 == len(iter_set)

            self.bar_plot(
                data=tmp,
                n=n,
                side=side,
                color=color,
                width=width,
                bar_width=bar_width,
                stat=stat,
                sets="KEGG",
                column=column,
                x_max=x_max,
                show_axis=show_axis,
                title=i,
                ax=ax,
            )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def REACTOME_plot(
        self,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n: int = 10,
        min_terms: int = 5,
        selected_parent: list = [],
        side="right",
        color="silver",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):
        """
        This method generates a bar plot for Reactome term enrichment and statistical analysis.

        Args:
            p_val (float) - significance threshold for p-values. Default is 0.05
            test (str) - statistical test to use ('FISH' - Fisher's Exact Test or 'BIN' - binomial test). Default is 'FISH'
            adj (str) - method for p-value adjustment ('BH' - Benjamini-Hochberg, 'BF' - Benjamini-Hochberg). Default is 'BH'
            n (int) - maximum number of terms to display per category. Default is 10
            min_terms (int) - minimum number of child terms required for a parent term to be included. Default is 5
            selected_parent (list) - list of specific parent terms to include in the plot. If empty, all parent terms are included. Default is []
            side (str) - side on which the bars are displayed ('left' or 'right'). Default is 'right'
            color (str) - color of the bars in the plot. Default is 'silver'
            width (int) - width of the plot in inches. Default is 10
            bar_width (float / int) - width of individual bars. Default is 0.5
            stat (str) - statistic to use for the x-axis ('p_val', 'n', or 'perc'). Default is 'p_val'

        Returns:
            fig (matplotlib.figure.Figure) - matplotlib Figure object containing the bar plots
        """

        sets = "REACTOME"
        column = "pathway"

        test_string = self.select_test(test, adj)

        tmp_in = pd.DataFrame(self.input_data["statistics"][sets])
        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"top_level_pathway_{test_string}"] <= p_val]
        tmp_in = tmp_in[tmp_in[f"pathway_{test_string}"] <= p_val]
        tmp_in[f"pathway_{test_string}"] = (
            tmp_in[f"pathway_{test_string}"]
            + np.min(
                tmp_in[f"pathway_{test_string}"][tmp_in[f"pathway_{test_string}"] != 0]
            )
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"pathway_{test_string}"])
        tmp_in = tmp_in.reset_index(drop=True)

        if stat.upper() == "perc".upper():
            x_max = np.max(tmp_in["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(tmp_in["-log(p-val)"])

        else:
            x_max = np.max(tmp_in["n"])

        # queue

        tmp_qq = tmp_in[["top_level_pathway", "-log(p-val)"]]

        tmp_qq["amount"] = tmp_qq["top_level_pathway"].map(
            tmp_qq["top_level_pathway"].value_counts()
        )

        tmp_qq = tmp_qq.groupby("top_level_pathway", as_index=False).agg(
            amount=("amount", "first"), avg_log_pval=("-log(p-val)", "mean")
        )

        tmp_qq = tmp_qq.sort_values(
            by=["amount", "avg_log_pval"], ascending=[False, False]
        ).reset_index(drop=True)

        #######################################################################
        iter_set = list(tmp_qq["top_level_pathway"])

        if len(selected_parent) > 0:
            tmp_iter = []
            for i in selected_parent:
                if i in iter_set:
                    tmp_iter.append(i)
                else:
                    print(f"\nParent term name: {i} was not found")

            iter_set = tmp_iter

            if len(iter_set) == 0:
                raise ValueError("Nothing to return")

        hlist = []

        valid_iter_set = []

        for l, it in enumerate(iter_set):

            inx = [x for x in tmp_in.index if it in tmp_in["top_level_pathway"][x]]
            tmp = tmp_in.loc[inx]

            if len(set(tmp[column])) >= min_terms:
                valid_iter_set.append(it)

                if float(len(set(tmp[column]))) > n:

                    tn = n
                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / 2.1)

                else:

                    tn = float(len(set(tmp[column])))

                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))

                    else:
                        hlist.append(tn / 2.1)

        iter_set = valid_iter_set

        fig = plt.figure(figsize=(width, sum(hlist)))

        gs = GridSpec(len(hlist), 1, height_ratios=hlist)
        gs.update(hspace=len(hlist) / 50)

        for l, i in enumerate(iter_set):
            inx = [x for x in tmp_in.index if i in tmp_in["top_level_pathway"][x]]
            tmp = tmp_in.loc[inx]

            ax = fig.add_subplot(gs[l])

            show_axis = l + 1 == len(iter_set)

            self.bar_plot(
                data=tmp,
                n=n,
                side=side,
                color=color,
                width=width,
                bar_width=bar_width,
                stat=stat,
                sets="REACTOME",
                column=column,
                x_max=x_max,
                show_axis=show_axis,
                title=i,
                ax=ax,
            )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def SPECIFICITY_plot(
        self,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n=5,
        side="right",
        color="bisque",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):
        """
        This method generates a bar plot for tissue specificity [Human Protein Atlas (HPA)] enrichment and statistical analysis.

        Args:
            p_val (float) - significance threshold for p-values. Default is 0.05
            test (str) - statistical test to use ('FISH' - Fisher's Exact Test or 'BIN' - binomial test). Default is 'FISH'
            adj (str) - method for p-value adjustment ('BH' - Benjamini-Hochberg, 'BF' - Benjamini-Hochberg). Default is 'BH'
            n (int) - maximum number of terms to display per category. Default is 5
            side (str) - side on which the bars are displayed ('left' or 'right'). Default is 'right'
            color (str) - color of the bars in the plot. Default is 'bisque'
            width (int) - width of the plot in inches. Default is 10
            bar_width (float / int) - width of individual bars. Default is 0.5
            stat (str) - statistic to use for the x-axis ('p_val', 'n', or 'perc'). Default is 'p_val'

        Returns:
            fig (matplotlib.figure.Figure) - matplotlib Figure object containing the bar plots
        """

        sets = "specificity"
        column = "specificity"

        test_string = self.select_test(test, adj)

        full_df = pd.DataFrame()

        for si in self.input_data["statistics"][sets].keys():

            tmp_in = pd.DataFrame(self.input_data["statistics"][sets][si])

            tmp_in = tmp_in[tmp_in[test_string] <= p_val]
            tmp_in[test_string] = (
                tmp_in[test_string]
                + np.min(tmp_in[test_string][tmp_in[test_string] != 0]) / 2
            )
            tmp_in["-log(p-val)"] = -np.log(tmp_in[test_string])
            tmp_in = tmp_in.reset_index(drop=True)
            tmp_in["set"] = si

            full_df = pd.concat([full_df, tmp_in])

        full_df = full_df.reset_index(drop=True)
        full_df["specificity"] = [
            x[0].upper() + x[1:] if isinstance(x, str) and len(x) > 0 else x
            for x in full_df["specificity"]
        ]

        if stat.upper() == "perc".upper():
            x_max = np.max(full_df["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(full_df["-log(p-val)"])

        else:
            x_max = np.max(full_df["n"])

        # queue

        tmp_qq = full_df[["set", "-log(p-val)"]]

        tmp_qq["amount"] = tmp_qq["set"].map(tmp_qq["set"].value_counts())

        tmp_qq = tmp_qq.groupby("set", as_index=False).agg(
            amount=("amount", "first"), avg_log_pval=("-log(p-val)", "mean")
        )

        tmp_qq = tmp_qq.sort_values(
            by=["amount", "avg_log_pval"], ascending=[False, False]
        ).reset_index(drop=True)

        #######################################################################
        iter_set = list(tmp_qq["set"])

        hlist = []
        for it in iter_set:
            print(it)
            inx = [x for x in full_df.index if it in full_df["set"][x]]
            tmp = full_df.loc[inx]
            if float(len(tmp[column])) > n:
                tn = n
                if tn < 6:
                    if tn < 2:
                        hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / (2.12 + ((6 - tn) / 10)))
                else:
                    hlist.append(tn / 2.1)

            else:
                tn = float(len(tmp[column]))
                if tn < 6:
                    if tn < 2:
                        hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / (2.12 + ((6 - tn) / 10)))

                else:
                    hlist.append(tn / 2.1)

        fig = plt.figure(figsize=(width, sum(hlist)))

        gs = GridSpec(len(hlist), 1, height_ratios=hlist)
        gs.update(hspace=len(hlist) / 50)

        for l, i in enumerate(iter_set):
            inx = [x for x in full_df.index if i in full_df["set"][x]]
            tmp = full_df.loc[inx]

            ax = fig.add_subplot(gs[l])

            show_axis = l + 1 == len(iter_set)

            self.bar_plot(
                data=tmp,
                n=n,
                side=side,
                color=color,
                width=width,
                bar_width=bar_width,
                stat=stat,
                sets="REACTOME",
                column=column,
                x_max=x_max,
                show_axis=show_axis,
                title=i,
                ax=ax,
            )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def DISEASES_plot(
        self,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n=5,
        side="right",
        color="thistle",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):
        """
        This method generates a bar plot for Human Diseases enrichment and statistical analysis.

        Args:
            p_val (float) - significance threshold for p-values. Default is 0.05
            test (str) - statistical test to use ('FISH' - Fisher's Exact Test or 'BIN' - binomial test). Default is 'FISH'
            adj (str) - method for p-value adjustment ('BH' - Benjamini-Hochberg, 'BF' - Benjamini-Hochberg). Default is 'BH'
            n (int) - maximum number of terms to display per category. Default is 5
            side (str) - side on which the bars are displayed ('left' or 'right'). Default is 'right'
            color (str) - color of the bars in the plot. Default is 'thistle'
            width (int) - width of the plot in inches. Default is 10
            bar_width (float / int) - width of individual bars. Default is 0.5
            stat (str) - statistic to use for the x-axis ('p_val', 'n', or 'perc'). Default is 'p_val'

        Returns:
            fig (matplotlib.figure.Figure) - matplotlib Figure object containing the bar plots
        """

        sets = "DISEASES"
        column = "disease"

        test_string = self.select_test(test, adj)

        tmp_in = pd.DataFrame(self.input_data["statistics"][sets])

        tmp_in = tmp_in[tmp_in[test_string] <= p_val]
        tmp_in[test_string] = (
            tmp_in[test_string]
            + np.min(tmp_in[test_string][tmp_in[test_string] != 0]) / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[test_string])
        tmp_in = tmp_in.reset_index(drop=True)
        tmp_in["disease"] = [
            x[0].upper() + x[1:] if isinstance(x, str) and len(x) > 0 else x
            for x in tmp_in["disease"]
        ]

        if stat.upper() == "perc".upper():
            x_max = np.max(tmp_in["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(tmp_in["-log(p-val)"])

        else:
            x_max = np.max(tmp_in["n"])

        # queue

        fig = self.bar_plot(
            data=tmp_in,
            n=n,
            side=side,
            color=color,
            width=width,
            bar_width=bar_width,
            stat=stat,
            sets="DISEASES",
            column=column,
            x_max=x_max,
            show_axis=True,
            title="DISEASES",
            ax=None,
        )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def ViMIC_plot(
        self,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n=5,
        side="right",
        color="aquamarine",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):
        """
        This method generates a bar plot for Viral Diseases (ViMIC) enrichment and statistical analysis.

        Args:
            p_val (float) - significance threshold for p-values. Default is 0.05
            test (str) - statistical test to use ('FISH' - Fisher's Exact Test or 'BIN' - binomial test). Default is 'FISH'
            adj (str) - method for p-value adjustment ('BH' - Benjamini-Hochberg, 'BF' - Benjamini-Hochberg). Default is 'BH'
            n (int) - maximum number of terms to display per category. Default is 5
            side (str) - side on which the bars are displayed ('left' or 'right'). Default is 'right'
            color (str) - color of the bars in the plot. Default is 'aquamarine'
            width (int) - width of the plot in inches. Default is 10
            bar_width (float / int) - width of individual bars. Default is 0.5
            stat (str) - statistic to use for the x-axis ('p_val', 'n', or 'perc'). Default is 'p_val'

        Returns:
            fig (matplotlib.figure.Figure) - matplotlib Figure object containing the bar plots
        """

        sets = "ViMIC"
        column = "virus"

        test_string = self.select_test(test, adj)

        tmp_in = pd.DataFrame(self.input_data["statistics"][sets])

        tmp_in = tmp_in[tmp_in[test_string] <= p_val]
        tmp_in[test_string] = (
            tmp_in[test_string]
            + np.min(tmp_in[test_string][tmp_in[test_string] != 0]) / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[test_string])
        tmp_in = tmp_in.reset_index(drop=True)

        if stat.upper() == "perc".upper():
            x_max = np.max(tmp_in["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(tmp_in["-log(p-val)"])

        else:
            x_max = np.max(tmp_in["n"])

        # queue

        fig = self.bar_plot(
            data=tmp_in,
            n=n,
            side=side,
            color=color,
            width=width,
            bar_width=bar_width,
            stat=stat,
            sets="ViMIC",
            column=column,
            x_max=x_max,
            show_axis=True,
            title="ViMIC",
            ax=None,
        )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def blod_markers_plot(
        self, n=10, side="right", color="red", width=10, bar_width=0.5
    ):
        """
        This method generates a bar plot for Blood Markers enrichment analysis.

        Args:
            p_val (float) - significance threshold for p-values. Default is 0.05
            n (int) - maximum number of terms to display per category. Default is 5
            side (str) - side on which the bars are displayed ('left' or 'right'). Default is 'right'
            color (str) - color of the bars in the plot. Default is 'red'
            width (int) - width of the plot in inches. Default is 10
            bar_width (float / int) - width of individual bars. Default is 0.5

        Returns:
            fig (matplotlib.figure.Figure) - matplotlib Figure object containing the bar plots
        """

        tmp_in = pd.DataFrame(self.input_data["enrichment"]["HPA"]["HPA_blood_markers"])

        x_max = max(
            np.log10(np.max(tmp_in["blood_concentration_IM[pg/L]"])),
            np.log10(np.max(tmp_in["blood_concentration_MS[pg/L]"])),
        )

        iter_set = ["blood_concentration_IM[pg/L]", "blood_concentration_MS[pg/L]"]

        hlist = []
        for it in iter_set:
            print(it)

            tmp_len = len(tmp_in[it][tmp_in[it] == tmp_in[it]])

            if float(tmp_len) > n:
                tn = n
                if tn < 6:
                    if tn < 2:
                        hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / (2.12 + ((6 - tn) / 10)))
                else:
                    hlist.append(tn / 2.1)

            else:
                tn = float(tmp_len)
                if tn < 6:
                    if tn < 2:
                        hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / (2.12 + ((6 - tn) / 10)))

                else:
                    hlist.append(tn / 2.1)

        fig = plt.figure(figsize=(width, sum(hlist)))

        gs = GridSpec(len(hlist), 1, height_ratios=hlist)

        gs.update(hspace=len(hlist) / 30)

        for l, i in enumerate(iter_set):

            tmp = tmp_in[tmp_in[i] == tmp_in[i]]

            tmp[i] = np.log10(tmp[i])

            ax = fig.add_subplot(gs[l])

            show_axis = l + 1 == len(iter_set)

            self.bar_plot_blood(
                data=tmp,
                n=n,
                side=side,
                color=color,
                width=width,
                bar_width=bar_width,
                stat=i,
                sets="Blood markers",
                column="found_names",
                x_max=x_max,
                show_axis=show_axis,
                title=f"log({i})",
                ax=ax,
            )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def GOPa_network_create(
        self,
        data_set: str = "GO-TERM",
        genes_inc: int = 10,
        gene_int: bool = True,
        genes_only: bool = True,
        min_con: int = 2,
        children_con: bool = False,
        include_childrend: bool = True,
        selected_parents: list = [],
        selected_genes: list = [],
    ):
        """
        This method creates a network graph for Gene Ontology (GO) or pathway analysis.

        Args:
            data_set (str) - type of data set to use for the network ['GO-TERM', 'KEGG', 'REACTOME']. Default is 'GO-TERM'
            genes_inc (int) - number of top genes to include in the network based on their occurrence. Default is 10
            gene_int (bool) - whether to include gene-gene interactions in the network. Default is True
            genes_only (bool) - whether to restrict the network to only include selected genes and their connections. Default is True
            min_con (int) - minimum number of connections required for a GO term or pathway to be included in the network. Default is 2.
            children_con (bool) - whether to include child connections in the network. Default is False
            include_childrend (bool) - whether to include children terms as nodes in the network. Default is True
            selected_parents (list) - specific parent terms to include in the network. If empty, all parents are considered. Default is []
            selected_genes (list) - specific genes to include in the network. If empty, all genes are considered. Default is []

        Returns:
            fig (networkx.Graph) - NetworkX Graph object representing the GO or pathway network
        """

        GOPa = pd.DataFrame(self.input_data["networks"][data_set])
        genes_list = list(set(GOPa["features"]))

        if len(selected_genes) > 0:
            to_select_genes = []
            for p in selected_genes:
                if p in list(GOPa["features"]):
                    to_select_genes.append(p)
                else:
                    print("\nCould not find {p} gene!")

            if len(to_select_genes) != 0:
                GOPa = GOPa[GOPa["features"].isin(to_select_genes)]
                genes_inc = max(genes_inc, len(to_select_genes))
            else:
                print("\nCould not use provided set of genes!")

        if data_set in ["GO-TERM", "KEGG", "REACTOME"]:

            GOPa_drop = GOPa[["parent", "children"]].drop_duplicates()

            GOPa_drop = Counter(list(GOPa_drop["parent"]))

            GOPa_drop = pd.DataFrame(GOPa_drop.items(), columns=["GOPa", "n"])

            GOPa_drop = list(GOPa_drop["GOPa"][GOPa_drop["n"] >= min_con])

            GOPa = GOPa[GOPa["parent"].isin(GOPa_drop)]

            del GOPa_drop

            if genes_inc > 0:

                genes_list = GOPa["features"]

                inter = None
                tmp_genes_list = []

                if gene_int:
                    inter = pd.DataFrame(self.input_data["statistics"]["interactions"])
                    inter = inter[inter["A"] != inter["B"]]
                    inter = inter[inter["A"].isin(genes_list)]
                    inter = inter[inter["B"].isin(genes_list)]
                    tmp_genes_list = list(set(list(inter["B"]) + list(inter["A"])))

                    if len(tmp_genes_list) > 0:
                        genes_list = tmp_genes_list

                genes_list = Counter(genes_list)

                genes_list = pd.DataFrame(genes_list.items(), columns=["features", "n"])

                genes_list = genes_list.sort_values("n", ascending=False)

                gene_GOPa_p = GOPa[["parent", "features"]][
                    GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
                ]
                gene_GOP_c = GOPa[["features", "children"]][
                    GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
                ]
                genes_list = list(genes_list["features"][:genes_inc])

                if genes_only:
                    GOPa = GOPa[GOPa["features"].isin(genes_list)]

                gene_GOPa_p.columns = ["parent", "children"]

                gene_GOPa_p["color"] = "gray"

                GOPa = pd.concat([GOPa[["parent", "children", "color"]], gene_GOPa_p])

                if len(tmp_genes_list) > 0:
                    if isinstance(inter, pd.DataFrame):
                        inter = inter[inter["A"].isin(genes_list)]
                        inter = inter[inter["B"].isin(genes_list)]
                        inter = inter[["A", "B"]]
                        inter.columns = ["parent", "children"]
                        inter["color"] = "red"

                        GOPa = pd.concat([GOPa, inter])

                if children_con:

                    gene_GOP_c.columns = ["parent", "children"]

                    gene_GOP_c["color"] = "gray"

                    GOPa = pd.concat(
                        [GOPa[["parent", "children", "color"]], gene_GOP_c]
                    )

                del gene_GOP_c, gene_GOPa_p

            gopa_list = list(GOPa["parent"]) + list(GOPa["children"])

            gopa_list = Counter(gopa_list)

            gopa_list = pd.DataFrame(gopa_list.items(), columns=["GOPa", "weight"])

            if len(selected_parents) > 0:
                to_select = []
                to_select_genes = []

                for p in selected_parents:
                    if p in list(GOPa["parent"]):
                        to_select.append(p)
                        t = list(GOPa["children"][GOPa["parent"] == p])
                        for i in t:
                            tg = [x for x in genes_list if x in list(GOPa["children"])]
                            if i in tg:
                                to_select_genes.append(i)

                    else:
                        print("\nCould not find {p} parent term!")

                if len(to_select) != 0:
                    GOPa = GOPa[
                        GOPa["parent"].isin(to_select + to_select_genes)
                        & GOPa["children"].isin(
                            list(GOPa["children"][GOPa["parent"].isin(to_select)])
                        )
                    ]
                    gopa_list = gopa_list[
                        gopa_list["GOPa"].isin(
                            list(GOPa["parent"]) + list(GOPa["children"])
                        )
                    ]

                else:
                    print("\nCould not use provided set of parent terms!")

            if include_childrend is False:
                GOPa = GOPa[GOPa["children"].isin(list(GOPa["parent"]) + genes_list)]
                gopa_list = gopa_list[
                    gopa_list["GOPa"].isin(list(GOPa["parent"]) + genes_list)
                ]

            G = nx.Graph()

            for _, row in gopa_list.iterrows():
                node = row["GOPa"]

                if node in genes_list:
                    color = "orange"
                    weight = np.log2(row["weight"] * 1000)

                elif node in list(GOPa["parent"]):
                    color = "cyan"
                    weight = np.log2(row["weight"] * 1000) * 2
                else:
                    color = "silver"
                    weight = np.log2(row["weight"] * 1000)

                G.add_node(node, size=weight, color=color)

            for _, row in GOPa.iterrows():
                source = row["parent"]
                target = row["children"]
                color = row["color"]
                G.add_edge(source, target, color=color)

            return G

        else:

            print("\nWrong data set selected!")
            print("\nAvaiable data sets are included in:")

            for i in ["GO-TERM", "KEGG", "DISEASES", "ViMIC", "REACTOME"]:
                print(f"\n{i}")

    def GI_network_create(self, min_con: int = 2):
        """
        This method creates a gene or protein interaction network graph.

        Args:
            min_con (int) - minimum number of connections (degree) required for a gene or protein to be included in the network. Default is 2

        Returns:
            fig (networkx.Graph) - NetworkX Graph object representing the interaction network, with nodes sized by connection count and edges colored by interaction type
        """

        inter = pd.DataFrame(self.input_data["statistics"]["interactions"])
        inter = inter[["A", "B", "connection_type"]]

        dict_meta = pd.DataFrame(
            {
                "interactions": [
                    ["gene -> gene"],
                    ["protein -> protein"],
                    ["gene -> protein"],
                    ["protein -> gene"],
                    ["gene -> gene", "protein -> protein"],
                    ["gene -> gene", "gene -> protein"],
                    ["gene -> gene", "protein -> gene"],
                    ["protein -> protein", "gene -> protein"],
                    ["protein -> protein", "protein -> gene"],
                    ["gene -> protein", "protein -> gene"],
                    ["gene -> gene", "protein -> protein", "gene -> protein"],
                    ["gene -> gene", "protein -> protein", "protein -> gene"],
                    ["gene -> gene", "gene -> protein", "protein -> gene"],
                    ["protein -> protein", "gene -> protein", "protein -> gene"],
                    [
                        "gene -> gene",
                        "protein -> protein",
                        "gene -> protein",
                        "protein -> gene",
                    ],
                ],
                "color": [
                    "#f67089",
                    "#f47832",
                    "#ca9213",
                    "#ad9d31",
                    "#8eb041",
                    "#4fb14f",
                    "#33b07a",
                    "#35ae99",
                    "#36acae",
                    "#38a9c5",
                    "#3aa3ec",
                    "#957cf4",
                    "#cd79f4",
                    "#f35fb5",
                    "#f669b7",
                ],
            }
        )

        genes_list = list(inter["A"]) + list(inter["B"])

        genes_list = Counter(genes_list)

        genes_list = pd.DataFrame(genes_list.items(), columns=["features", "n"])

        genes_list = genes_list.sort_values("n", ascending=False)

        genes_list = genes_list[genes_list["n"] >= min_con]

        inter = inter[inter["A"].isin(list(genes_list["features"]))]
        inter = inter[inter["B"].isin(list(genes_list["features"]))]

        inter = inter.groupby(["A", "B"]).agg({"connection_type": list}).reset_index()

        inter["color"] = "black"

        for inx in inter.index:
            for inx2 in dict_meta.index:
                if set(inter["connection_type"][inx]) == set(
                    dict_meta["interactions"][inx2]
                ):
                    inter["color"][inx] = dict_meta["color"][inx2]
                    break

        G = nx.Graph()

        for _, row in genes_list.iterrows():
            node = row["features"]
            color = "khaki"
            weight = np.log2(row["n"] * 500)
            G.add_node(node, size=weight, color=color)

        for _, row in inter.iterrows():
            source = row["A"]
            target = row["B"]
            color = row["color"]
            G.add_edge(source, target, color=color)

        return G

    def AUTO_ML_network(
        self,
        genes_inc: int = 10,
        gene_int: bool = True,
        genes_only: bool = True,
        min_con: int = 2,
        children_con: bool = False,
        include_childrend: bool = False,
        selected_parents: list = [],
        selected_genes: list = [],
    ):
        """
        This method creates a machine learning supported multi-layered network of gene or protein interactions using GO-TERM, KEGG, and REACTOME data.

        Args:
            genes_inc (int) - number of top genes to include based on interaction frequency. Default is 10
            genes_inc (int) - number of top genes to include in the network based on their occurrence. Default is 10
            gene_int (bool) - whether to include gene-gene interactions in the network. Default is True
            genes_only (bool) - whether to restrict the network to only include selected genes and their connections. Default is True
            min_con (int) - minimum number of connections required for a GO term or pathway to be included in the network. Default is 2.
            children_con (bool) - whether to include child connections in the network. Default is False
            include_childrend (bool) - whether to include children terms as nodes in the network. Default is True
            selected_parents (list) - specific parent terms to include in the network. If empty, all parents are considered. Default is []
            selected_genes (list) - specific genes to include in the network. If empty, all genes are considered. Default is []

        Returns
           Returns:
               fig (networkx.Graph) - NetworkX Graph object representing the GO and pathway network
        """

        full_genes = []
        genes_sets = []
        GOPa = pd.DataFrame()
        for s in ["GO-TERM", "KEGG", "REACTOME"]:
            if s in self.input_data["networks"].keys():
                genes_sets.append(set(self.input_data["networks"][s]["features"]))
                full_genes += list(set(self.input_data["networks"][s]["features"]))
                tmp = pd.DataFrame(self.input_data["networks"][s])
                tmp["set"] = s
                tmp["color"] = "gray"
                GOPa = pd.concat([GOPa, tmp])

        common_elements = set.intersection(*genes_sets)

        del genes_sets

        inter = pd.DataFrame(self.input_data["statistics"]["interactions"])
        inter = inter[inter["A"].isin(full_genes)]
        inter = inter[inter["B"].isin(full_genes)]

        if len(common_elements) > 0:
            inter = inter[
                inter["A"].isin(common_elements) | inter["B"].isin(common_elements)
            ]

        selection_list = list(set(list(set(inter["B"])) + list(set(inter["A"]))))

        if len(selected_genes) > 0:
            to_select_genes = []
            for p in selected_genes:
                if p in list(GOPa["features"]):
                    to_select_genes.append(p)
                else:
                    print("\nCould not find {p} gene!")

            if len(to_select_genes) != 0:
                GOPa = GOPa[GOPa["features"].isin(to_select_genes)]
                genes_inc = max(genes_inc, len(to_select_genes))

            else:
                print("\nCould not use provided set of genes!")

        else:
            GOPa = GOPa[GOPa["features"].isin(selection_list)]

        GOPa_drop = GOPa[["parent", "children"]].drop_duplicates()

        GOPa_drop = Counter(list(GOPa_drop["parent"]))

        GOPa_drop = pd.DataFrame(GOPa_drop.items(), columns=["GOPa", "n"])

        GOPa_drop = list(GOPa_drop["GOPa"][GOPa_drop["n"] >= min_con])

        GOPa = GOPa[GOPa["parent"].isin(GOPa_drop)]

        del GOPa_drop

        if genes_inc > 0:

            genes_list = GOPa["features"]

            inter = None
            tmp_genes_list = []

            if gene_int:
                inter = pd.DataFrame(self.input_data["statistics"]["interactions"])
                inter = inter[inter["A"] != inter["B"]]
                inter = inter[inter["A"].isin(genes_list)]
                inter = inter[inter["B"].isin(genes_list)]
                tmp_genes_list = list(set(list(inter["B"]) + list(inter["A"])))

                if len(tmp_genes_list) > 0:
                    genes_list = tmp_genes_list

            genes_list = Counter(genes_list)

            genes_list = pd.DataFrame(genes_list.items(), columns=["features", "n"])

            genes_list = genes_list.sort_values("n", ascending=False)

            gene_GOPa_p = GOPa[["parent", "features", "set", "color"]][
                GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
            ]
            gene_GOP_c = GOPa[["features", "children", "set", "color"]][
                GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
            ]
            genes_list = list(genes_list["features"][:genes_inc])

            if genes_only:
                GOPa = GOPa[GOPa["features"].isin(genes_list)]

            gene_GOPa_p.columns = ["parent", "children", "set", "color"]

            GOPa = pd.concat(
                [GOPa[["parent", "children", "set", "color"]], gene_GOPa_p]
            )

            if len(tmp_genes_list) > 0:
                if isinstance(inter, pd.DataFrame):
                    inter = inter[inter["A"].isin(genes_list)]
                    inter = inter[inter["B"].isin(genes_list)]
                    inter = inter[["A", "B"]]
                    inter.columns = ["parent", "children"]
                    inter["set"] = "gene"
                    inter["color"] = "red"

                    GOPa = pd.concat([GOPa, inter])

            if children_con:

                gene_GOP_c.columns = ["parent", "children", "set", "color"]

                GOPa = pd.concat(
                    [GOPa[["parent", "children", "set", "color"]], gene_GOP_c]
                )

            del gene_GOP_c, gene_GOPa_p

        gopa_list = list(GOPa["parent"]) + list(GOPa["children"])

        gopa_list = Counter(gopa_list)

        gopa_list = pd.DataFrame(
            gopa_list.items(), columns=["GOPa", "weight"]
        ).reset_index(drop=True)

        gopa_list["set"] = None

        for inx in gopa_list.index:
            if gopa_list["GOPa"][inx] in list(GOPa["parent"]):
                gopa_list["set"][inx] = list(
                    GOPa["set"][GOPa["parent"] == gopa_list["GOPa"][inx]]
                )[0]
            elif gopa_list["GOPa"][inx] in list(GOPa["children"]):
                gopa_list["set"][inx] = list(
                    GOPa["set"][GOPa["children"] == gopa_list["GOPa"][inx]]
                )[0]

        if len(selected_parents) > 0:
            to_select = []
            to_select_genes = []

            for p in selected_parents:
                if p in list(GOPa["parent"]):
                    to_select.append(p)
                    t = list(GOPa["children"][GOPa["parent"] == p])
                    for i in t:
                        tg = [x for x in genes_list if x in list(GOPa["children"])]
                        if i in tg:
                            to_select_genes.append(i)

                else:
                    print("\nCould not find {p} parent term!")

            if len(to_select) != 0:
                GOPa = GOPa[
                    GOPa["parent"].isin(to_select + to_select_genes)
                    & GOPa["children"].isin(
                        list(GOPa["children"][GOPa["parent"].isin(to_select)])
                    )
                ]
                gopa_list = gopa_list[
                    gopa_list["GOPa"].isin(
                        list(GOPa["parent"]) + list(GOPa["children"])
                    )
                ]

            else:
                print("\nCould not use provided set of parent terms!")

        if include_childrend is False:
            GOPa = GOPa[GOPa["children"].isin(list(GOPa["parent"]) + genes_list)]
            gopa_list = gopa_list[
                gopa_list["GOPa"].isin(list(GOPa["parent"]) + genes_list)
            ]

        G = nx.Graph()

        for _, row in gopa_list.iterrows():
            node = row["GOPa"]

            color = "black"

            if node in genes_list:
                color = "orange"
                weight = np.log2(row["weight"] * 1000)

            elif node in list(GOPa["parent"]):
                color = "cyan"
                weight = np.log2(row["weight"] * 1000) * 2

            else:
                if row["set"] == "GO-TERM":
                    color = "bisque"
                    weight = np.log2(row["weight"] * 1000)

                elif row["set"] == "KEGG":
                    color = "mistyrose"
                    weight = np.log2(row["weight"] * 1000)

                elif row["set"] == "REACTOME":
                    color = "darkkhaki"
                    weight = np.log2(row["weight"] * 1000)

            G.add_node(node, size=weight, color=color)

        for _, row in GOPa.iterrows():
            source = row["parent"]
            target = row["children"]
            color = row["color"]
            G.add_edge(source, target, color=color)

        return G

    def gene_scatter(
        self,
        colors="viridis",
        species="human",
        hclust="complete",
        img_width=None,
        img_high=None,
        label_size=None,
        x_lab="Genes",
        legend_lab="log(TPM + 1)",
        selected_list: list = [],
    ):
        """
        Visualizes RNA-SEQ enrichment data using scatter plots with hierarchical clustering.

        RNA-SEQ data including:
           -human_tissue_expression_HPA
           -human_tissue_expression_RNA_total_tissue
           -human_tissue_expression_fetal_development_circular

        Args:
            colors (str) - colormap used for scatter plot points. Default is 'viridis'
            species (str) - determines the case formatting of tissue labels. Use 'human' for uppercase labels, or other values for title case. Default is 'human'
            hclust (str) - hierarchical clustering method applied to reorder rows and columns. Options include 'single', 'complete', 'average', etc. Default is 'complete'
            img_width (int / None) - width of the output image in inches. If None, the width is determined based on the number of genes. Default is None
            img_high (int / None) - height of the output image in inches. If None, the height is determined based on the number of tissues. Default is None
            label_size (int / None) - font size for axis labels and tick marks. Calculated dynamically if None. Default is None
            x_lab (str) - label for the x-axis. Default is 'Genes'
            legend_lab (str,) - label for the color bar legend. Default is 'log(TPM + 1)'
            selected_list (list) - list of specific genes to include in the visualization. If left empty, all genes from the dataset will be displayed. Default is []

        Returns:
            return_dict (dict) - dictionary with dataset names as keys and their corresponding matplotlib figures as values. Each figure shows a scatter plot of the different RNAseq data
        """

        input_data = self.input_data["enrichment"]["RNA-SEQ"]

        return_dict = {}

        for i in input_data.keys():
            data = pd.DataFrame(input_data[i])
            data.index = data["tissue"]
            data.pop("tissue")

            if len(selected_list) > 0:
                selected_list = [y.upper() for y in selected_list]
                to_select = [x for x in data.columns if x.upper() in selected_list]
                data = data.loc[:, to_select]

            scatter_df = data

            if img_width is None:
                img_width = len(scatter_df.columns) * 1.2

            if img_high is None:
                img_high = len(scatter_df.index) * 0.9

            if label_size is None:
                label_size = np.log(len(scatter_df.index) * len(scatter_df.index)) * 2.5

                if label_size < 7:
                    label_size = 7

            cm = 1 / 2.54

            if len(scatter_df) > 1:

                Z = linkage(scatter_df, method=hclust)

                # Get the order of features based on the dendrogram
                order_of_features = dendrogram(Z, no_plot=True)["leaves"]

                indexes_sort = list(scatter_df.index)
                sorted_list_rows = []
                for n in order_of_features:
                    sorted_list_rows.append(indexes_sort[n])

                scatter_df = scatter_df.transpose()

                Z = linkage(scatter_df, method=hclust)

                # Get the order of features based on the dendrogram
                order_of_features = dendrogram(Z, no_plot=True)["leaves"]

                indexes_sort = list(scatter_df.index)
                sorted_list_columns = []
                for n in order_of_features:
                    sorted_list_columns.append(indexes_sort[n])

                scatter_df = scatter_df.transpose()

                scatter_df = scatter_df.loc[sorted_list_rows, sorted_list_columns]

            scatter_df = np.log(scatter_df + 1)
            scatter_df[scatter_df <= np.mean(scatter_df.quantile(0.10))] = (
                np.mean(np.mean(scatter_df, axis=1)) / 10
            )

            if species.lower() == "human":
                scatter_df.index = [x.upper() for x in scatter_df.index]
            else:
                scatter_df.index = [x.title() for x in scatter_df.index]

            scatter_df.insert(0, "  ", 0)

            # Add a column of zeros at the end
            scatter_df[" "] = 0

            fig, ax = plt.subplots(figsize=(img_width * cm, img_high * cm))

            plt.scatter(
                x=[*range(0, len(scatter_df.columns), 1)],
                y=[" "] * len(scatter_df.columns),
                s=0,
                cmap=colors,
                edgecolors=None,
            )

            for index, row in enumerate(scatter_df.index):
                x = [*range(0, len(np.array(scatter_df.loc[row,])), 1)]
                y = [row] * len(x)
                s = np.array(scatter_df.loc[row,])
                plt.scatter(
                    x,
                    y,
                    s=np.log(s + 1) * 70,
                    c=s,
                    cmap=colors,
                    edgecolors="black",
                    vmin=np.array(scatter_df).min(),
                    vmax=np.array(scatter_df).max(),
                    linewidth=0.00001,
                )
                sm = plt.cm.ScalarMappable(cmap=colors)
                sm.set_clim(
                    vmin=np.array(scatter_df).min(), vmax=np.array(scatter_df).max()
                )
                plt.xticks(x, scatter_df.columns)
                plt.ylabel(str(x_lab), fontsize=label_size)

            plt.scatter(
                x=[*range(0, len(scatter_df.columns), 1)],
                y=[""] * len(scatter_df.columns),
                s=0,
                cmap=colors,
                edgecolors=None,
            )

            plt.xticks(rotation=80)
            plt.tight_layout()
            plt.margins(0.005)
            plt.xticks(fontsize=label_size)
            plt.yticks(fontsize=label_size)

            len_bar = ax.get_position().height / 5
            if len(scatter_df) < 15:
                len_bar = 0.65

                cbar = fig.colorbar(sm, ax=ax)
                cbar.ax.set_ylabel(str(legend_lab), fontsize=label_size * 0.9)
                cbar.ax.yaxis.set_ticks_position("right")
                cbar.ax.set_position(
                    [
                        ax.get_position().x1 + 0.05,
                        (ax.get_position().y0 + ax.get_position().y1) / 1.9,
                        ax.get_position().width / 0.05,
                        len_bar,
                    ]
                )
                cbar.ax.yaxis.set_label_position("right")
                cbar.ax.yaxis.set_tick_params(labelsize=label_size * 0.8)
                cbar.outline.set_edgecolor("none")
            else:
                cbar = fig.colorbar(sm, ax=ax)
                cbar.ax.set_ylabel(str(legend_lab), fontsize=label_size * 0.9)
                cbar.ax.yaxis.set_ticks_position("right")
                cbar.ax.set_position(
                    [
                        ax.get_position().x1 + 0.05,
                        (ax.get_position().y0 + ax.get_position().y1) / 1.45,
                        ax.get_position().width / 0.05,
                        len_bar,
                    ]
                )
                cbar.ax.yaxis.set_label_position("right")
                cbar.ax.yaxis.set_tick_params(labelsize=label_size * 0.8)
                cbar.outline.set_edgecolor("none")

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["bottom"].set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.xaxis.set_tick_params(length=0, labelbottom=True)
            ax.yaxis.set_tick_params(length=0, labelbottom=True)
            ax.grid(False)

            if self.show_plot:
                plt.show()
            elif self.show_plot is False:
                plt.close(fig)

            return_dict[i] = fig

        return return_dict


class DSA(PathMetadata):
    """
    The 'DSA' class performs Differential Set Analysis by taking the results from two independent feature lists (e.g., upregulated and downregulated genes).
    It utilizes input data derived from independent gene sets obtained through statistical and network analyses, which are part of the Analysis class results.
    These results are accessed using the 'self.get_full_results' method.


    Args:
        set1 (dict)- output data from the `Analysis` class `self.get_full_results` method of genes set eg. ['KIT', 'EDNRB', 'PAX3']
        set2 (dict)- output data from the `Analysis` class `self.get_full_results` method of genes set eg. ['MC4R', 'MITF', 'SLC2A4']
    """

    def __init__(self, set_1: dict, set_2: dict):

        super().__init__()

        def merge_dict_values(d1, d2):
            out = d1.copy()
            for k, v in d2.items():
                if k in out:
                    if isinstance(out[k], dict) and isinstance(v, dict):
                        out[k] = merge_dict_values(out[k], v)
                    elif isinstance(out[k], list) and isinstance(v, list):
                        out[k] = out[k] + v
                    else:
                        out[k] = v
                else:
                    out[k] = v
            return out

        self.set_1 = set_1
        self.set_2 = set_2

        if (
            self.set_1["enrichment"]["species"]["species_genes"]
            != self.set_2["enrichment"]["species"]["species_genes"]
        ):
            raise ValueError(
                "The 'self.species_genes' attribute used for enrichment analysis differed between set_1 and set_2."
            )

        if (
            self.set_1["enrichment"]["species"]["species_study"]
            != self.set_2["enrichment"]["species"]["species_study"]
        ):
            raise ValueError(
                "The 'self.species_study' attribute used for enrichment analysis differed between set_1 and set_2."
            )

        if (
            self.set_1["statistics"]["setup"]["network_stat"]
            != self.set_2["statistics"]["setup"]["network_stat"]
        ):
            raise ValueError(
                "The 'self.network_stat' attribute used for analysis differed between set_1 and set_2."
            )

        if (
            self.set_1["statistics"]["setup"]["go_grade"]
            != self.set_2["statistics"]["setup"]["go_grade"]
        ):
            raise ValueError(
                "The 'self.go_grade' attribute used for analysis differed between set_1 and set_2."
            )

        if (
            self.set_1["statistics"]["setup"]["interaction_strength"]
            != self.set_2["statistics"]["setup"]["interaction_strength"]
        ):
            raise ValueError(
                "The 'self.interaction_strength' attribute used for analysis differed between set_1 and set_2."
            )

        if (
            self.set_1["statistics"]["setup"]["interaction_source"]
            != self.set_2["statistics"]["setup"]["interaction_source"]
        ):
            raise ValueError(
                "The 'self.interaction_source' attribute used for analysis differed between set_1 and set_2."
            )

        self.min_fc = 1.25
        self.s1_genes = len(self.set_1["enrichment"]["gene_info"]["sid"])
        self.s2_genes = len(self.set_2["enrichment"]["gene_info"]["sid"])
        self.GO = None
        self.KEGG = None
        self.REACTOME = None
        self.specificity = None
        self.GI = None
        self.networks = None
        self.spec_over = None
        self.REACTOME_over = None
        self.KEGG_over = None
        self.GO_over = None
        self.inter_terms = None
        self.lr_con_set1_set2 = None
        self.lr_con_set2_set1 = None

        print("Enrichment process...")

        def merge_dict_values(d1, d2):
            out = d1.copy()
            for k, v in d2.items():
                if k in out:
                    if isinstance(out[k], dict) and isinstance(v, dict):
                        out[k] = merge_dict_values(out[k], v)
                    elif isinstance(out[k], list) and isinstance(v, list):
                        out[k] = out[k] + v
                    else:
                        out[k] = v
                else:
                    out[k] = v
            return out

        res = merge_dict_values(self.set_1["enrichment"], self.set_2["enrichment"])

        print("Calculation process...")

        ans = Analysis(res)

        del res

        ans.network_stat = self.set_1["statistics"]["setup"]["network_stat"]

        ans.go_grade = self.set_1["statistics"]["setup"]["go_grade"]

        ans.interaction_strength = self.set_1["statistics"]["setup"][
            "interaction_strength"
        ]

        ans.interaction_source = self.set_1["statistics"]["setup"]["interaction_source"]

        if "REACTOME" in self.set_1["statistics"].keys():
            ans.REACTOME_overrepresentation()
            self.REACTOME_over = ans.get_REACTOME_statistics()
            ans.REACTOME_network()
            self.REACTOME_net = pd.DataFrame(ans.get_REACTOME_network())

        if "KEGG" in self.set_1["statistics"].keys():
            ans.KEGG_overrepresentation()
            self.KEGG_over = ans.get_KEGG_statistics()
            ans.KEGG_network()
            self.KEGG_net = pd.DataFrame(ans.get_KEGG_network())

        if "GO-TERM" in self.set_1["statistics"].keys():
            ans.GO_overrepresentation()
            self.GO_over = ans.get_GO_statistics()
            ans.GO_network()
            self.GO_net = pd.DataFrame(ans.get_GO_network())

        ans.features_specificity()
        self.spec_over = ans.get_specificity_statistics()

        ans.gene_interaction()
        self.features_interactions_statistics = pd.DataFrame(
            ans.get_features_interactions_statistics()
        )

        print("Calculating intersections...")

        self.inter_processes()

        del ans

    def deserialize_data(self, value):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def set_min_fc(self, fc):
        """
        This method set 'self.min_fc' value, which is necessary for conducting Differential Set Analysis (DSA).
        The value must be numeric and greater than 1.

        Overview:
            The DSA method assesses differences between set1 and set2 by calculating the normalized occurrence ('n_occ') of each term in both sets and determining the Fold Change (FC) between these occurrences.
            For term that is absent in one of sets, their normalized occurrence ('n_occ') is assigned a value equal to half the minimum 'n_occ' observed across all terms within the analysis type (e.g., GO-TERM, KEGG, etc.).
            By analyzing these FC values, the method identifies key differences in enrichment between the two sets, highlighting biologically significant pathways or terms unique or equal to each set.

        Formulas:
            The normalized occurrence ('n_occ') for each term is calculated as:
               n_occ = genes per term / total genes per set

            The Fold Change (FC) is then computed as the ratio of normalized occurrences:
               FC = set1 n_occ / set2 n_occ


        Interpretation:
           - If FC > self.min_fc, the term is considered more enriched in set1
           - If FC < 1/self.min_fc, the term is considered more enriched in set2
           - If FC < self.min_fc and > 1/self.min_fc, the term is equal between sets

        Args:
            fc (float) - Fold Change threshold value to be set. The value must be numeric and greater than 1. Default is 1.5.
        """

        if not isinstance(fc, (int, float)):
            raise ValueError("fc must be a numeric value.")
        if fc <= 1:
            raise ValueError("fc must be greater than 1.")
        else:
            self.min_fc = fc

    def get_set_to_set_con(self):
        """
        This method returns the CellTalk/CellPhone (CellConnecctions) Differential Set Analysis (DSA)

        Returns:
            Returns dict {'set1->set2':'self.lr_con_set1_set2', 'set2->set1':'self.lr_con_set2_set1'} contains CellConnecctions DSA obtained using the `self.connections_diff` method.
        """

        cell_con = {}
        cell_con["set1->set2"] = self.lr_con_set1_set2
        cell_con["set2->set1"] = self.lr_con_set2_set1

        return cell_con

    def get_full_GO(self):
        """
        This method returns the concatenated GO-TERM data from set1 and set2.

        Returns:
            The concatenated data stored in
            `self.set_1['statistics']['GO-TERM']` and
            `self.set_2['statistics']['GO-TERM']`.
        """

        t1 = pd.DataFrame(self.set_1["statistics"]["GO-TERM"])
        t1["set"] = "s1"
        t2 = pd.DataFrame(self.set_2["statistics"]["GO-TERM"])
        t2["set"] = "s2"

        df = pd.concat([t1, t2]).reset_index(drop=True)

        return df

    def get_full_KEGG(self):
        """
        This method returns the concatenated KEGG data from set1 and set2.

        Returns:
            The concatenated data stored in
            `self.set_1['statistics']['KEGG']` and
            `self.set_2['statistics']['KEGG']`.
        """

        t1 = pd.DataFrame(self.set_1["statistics"]["KEGG"])
        t1["set"] = "s1"
        t2 = pd.DataFrame(self.set_2["statistics"]["KEGG"])
        t2["set"] = "s2"

        df = pd.concat([t1, t2]).reset_index(drop=True)

        return t2

    def get_full_REACTOME(self):
        """
        This method returns the concatenated REACTOME data from set1 and set2.

        Returns:
            The concatenated data stored in
            `self.set_1['statistics']['REACTOME']` and
            `self.set_2['statistics']['REACTOME']`.
        """

        t1 = pd.DataFrame(self.set_1["statistics"]["REACTOME"])
        t1["set"] = "s1"
        t2 = pd.DataFrame(self.set_2["statistics"]["REACTOME"])
        t2["set"] = "s2"

        df = pd.concat([t1, t2]).reset_index(drop=True)

        return t2

    def get_full_DISEASES(self):
        """
        This method returns the concatenated human disease data from set1 and set2.

        Returns:
            The concatenated data stored in
            `self.set_1['statistics']['DISEASES']` and
            `self.set_2['statistics']['DISEASES']`.
        """

        t1 = pd.DataFrame(self.set_1["statistics"]["DISEASES"])
        t1["set"] = "s1"
        t2 = pd.DataFrame(self.set_2["statistics"]["DISEASES"])
        t2["set"] = "s2"

        df = pd.concat([t1, t2]).reset_index(drop=True)

        return t2

    def get_full_ViMIC(self):
        """
        This method returns the concatenated ViMic viral data from set1 and set2.

        Returns:
            The concatenated data stored in
            `self.set_1['statistics']['ViMIC']` and
            `self.set_2['statistics']['ViMIC']`.
        """

        t1 = pd.DataFrame(self.set_1["statistics"]["ViMIC"])
        t1["set"] = "s1"
        t2 = pd.DataFrame(self.set_2["statistics"]["ViMIC"])
        t2["set"] = "s2"

        df = pd.concat([t1, t2]).reset_index(drop=True)

        return t2

    def get_full_SPECIFICITY(self):
        """
        This method returns the concatenated HPA specificity data from set1 and set2.

        Returns:
            The concatenated data stored in
            `self.set_1['statistics']['specificity']` and
            `self.set_2['statistics']['specificity']`.
        """

        t1 = pd.DataFrame(self.set_1["statistics"]["specificity"])
        t1["set"] = "s1"
        t2 = pd.DataFrame(self.set_2["statistics"]["specificity"])
        t2["set"] = "s2"

        df = pd.concat([t1, t2]).reset_index(drop=True)

        return t2

    def get_GO_diff(self):
        """
        This method returns the GO-TERM Differential Set Analysis (DSA)

        Returns:
            Returns `self.GO` contains GO-TERM DSA obtained using the `self.GO_diff` method.
        """

        return self.GO.to_dict(orient="list")

    def get_KEGG_diff(self):
        """
        This method returns the KEGG Differential Set Analysis (DSA)

        Returns:
            Returns `self.KEGG contains KEGG DSA obtained using the `self.KEGG_diff` method.
        """

        return self.KEGG.to_dict(orient="list")

    def get_REACTOME_diff(self):
        """
        This method returns the Reactome Differential Set Analysis (DSA)

        Returns:
            Returns `self.REACTOME` contains Reactome DSA obtained using the `self.REACTOME_diff` method.
        """

        return self.REACTOME.to_dict(orient="list")

    def get_specificity_diff(self):
        """
        This method returns the specificity (HPA) Differential Set Analysis (DSA)

        Returns:
            Returns `self.specificity` contains specificity DSA obtained using the `self.get_specificity_diff` method.
        """

        return self.specificity.to_dict(orient="list")

    def get_GI_diff(self):
        """
        This method returns the Genes Interactions (GI) Differential Set Analysis (DSA)

        Returns:
            Returns `self.GI` contains GO-TERM DSA obtained using the `self.gi_diff` method.
        """

        return self.GI.to_dict(orient="list")

    def get_networks_diff(self):
        """
        This method returns the network Differential Set Analysis (DSA)

        Returns:
            Returns `self.networks` contains network DSA obtained using the `self.get_networks_diff` method.
        """

        return self.networks

    def get_inter_terms(self):
        """
        This method returns the Inter Terms analysis results.

        Returns:
            Returns `self.inter_terms` contains Inter Terms analysis results obtained using the `self.inter_processes` method.
        """

        return self.inter_terms

    def GO_diff(self):
        """
        This method performs a Differential Set Analysis (DSA) to compare two sets (set1 and set2) based on their Gene Ontology (GO-TERM) enrichment analysis.

        Overview:
            This method assesses differences between set1 and set2 by calculating the normalized occurrence ('n_occ') of each term in both sets and determining the Fold Change (FC) between these occurrences.
            For term that is absent in one of sets, their normalized occurrence ('n_occ') is assigned a value equal to half the minimum 'n_occ' observed across all terms within the analysis type (e.g., GO-TERM, KEGG, etc.).
            By analyzing these FC values, the method identifies key differences in enrichment between the two sets, highlighting biologically significant pathways or terms unique or equal to each set.

        Formulas:
            The normalized occurrence ('n_occ') for each term is calculated as:
               n_occ = genes per term / total genes per set

            The Fold Change (FC) is then computed as the ratio of normalized occurrences:
               FC = set1 n_occ / set2 n_occ


        Interpretation:
           - If FC > self.min_fc, the term is considered more enriched in set1
           - If FC < 1/self.min_fc, the term is considered more enriched in set2
           - If FC < self.min_fc and > 1/self.min_fc, the term is equal between sets

        Returns:
            Updates `self.GO` with Reactome DSA data.
            To retrieve the results, use the `self.get_GO_diff` method.
        """

        # parent check

        parent_columns = "parent_name"
        parent_n = "parent_n"

        children_columns = "child_name"
        children_n = "child_n"

        sets = "GO-TERM"

        s1_tmp = pd.DataFrame(self.set_1["statistics"][sets])
        s2_tmp = pd.DataFrame(self.set_2["statistics"][sets])

        #######################################################################

        set_1_list = self.set_1["enrichment"]["gene_info"]["found_names"]
        set_2_list = self.set_2["enrichment"]["gene_info"]["found_names"]

        inter_tmp = pd.DataFrame(self.inter_terms[sets])

        inter_tmp = inter_tmp.explode("child_genes")
        inter_tmp = inter_tmp.explode("parent_genes")

        inter_tmp["set_parent"] = None
        inter_tmp["set_children"] = None

        inter_tmp.loc[inter_tmp["child_genes"].isin(set_1_list), "set_children"] = (
            "set1"
        )
        inter_tmp.loc[inter_tmp["child_genes"].isin(set_2_list), "set_children"] = (
            "set2"
        )

        inter_tmp.loc[inter_tmp["parent_genes"].isin(set_1_list), "set_parent"] = "set1"
        inter_tmp.loc[inter_tmp["parent_genes"].isin(set_2_list), "set_parent"] = "set2"

        group_cols = ["parent_name", "child_name", "set"]

        agg_dict = {
            "child_genes": lambda x: list(set(x)),
            "parent_genes": lambda x: list(set(x)),
            "set_parent": lambda x: list(set(x)),
            "set_children": lambda x: list(set(x)),
            **{
                col: "first"
                for col in inter_tmp.columns
                if col
                not in group_cols
                + ["child_genes", "parent_genes", "set_parent", "set_children"]
            },
        }

        inter_tmp = inter_tmp.groupby(group_cols, as_index=False).agg(agg_dict)

        inter_tmp["set"] = inter_tmp["set_parent"] + inter_tmp["set_children"]
        inter_tmp["set"] = [list(set(x)) for x in inter_tmp["set"]]
        inter_tmp = inter_tmp.explode("set_children")

        inter_tmp = inter_tmp[
            inter_tmp["set"].apply(lambda x: isinstance(x, (list, set)) and len(x) > 1)
        ]

        if len(inter_tmp) > 0:

            s1_tmp = pd.concat(
                [s1_tmp, inter_tmp[inter_tmp["set_children"] == "set1"]]
            ).reset_index(drop=True)

            s1_tmp = s1_tmp.drop(columns=["set_children", "set_parent", "set"])

            s2_tmp = pd.concat(
                [s2_tmp, inter_tmp[inter_tmp["set_children"] == "set2"]]
            ).reset_index(drop=True)

            s2_tmp = s2_tmp.drop(columns=["set_children", "set_parent", "set"])

            self.set_1["statistics"][sets] = s1_tmp.to_dict(orient="list")
            self.set_2["statistics"][sets] = s2_tmp.to_dict(orient="list")

        #######################################################################

        term = []
        norm_n = []

        for s1 in set(s1_tmp[parent_columns]):

            term.append(s1)
            norm_n.append(
                float(np.mean(s1_tmp[parent_n][s1_tmp[parent_columns] == s1]))
                / self.s1_genes
            )

        s1 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        norm_n = []

        for s2 in set(s2_tmp[parent_columns]):

            term.append(s2)
            norm_n.append(
                float(np.mean(s2_tmp[parent_n][s2_tmp[parent_columns] == s2]))
                / self.s2_genes
            )

        s2 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        FC = []
        dec = []

        terms_s1 = set(s1["term"])
        terms_s2 = set(s2["term"])

        norm_s1 = dict(zip(s1["term"], s1["norm_n"]))
        norm_s2 = dict(zip(s2["term"], s2["norm_n"]))

        all_terms = terms_s1.union(terms_s2)

        min_value = min(list(norm_s1.values()) + list(norm_s2.values())) / 10

        for g in all_terms:
            if g in terms_s1 and g in terms_s2:
                fc_value = norm_s1[g] / norm_s2[g]
                if fc_value >= self.min_fc:
                    decision = "s1"
                elif fc_value <= 1 / self.min_fc:
                    decision = "s2"
                else:
                    decision = "inter"
            elif g in terms_s1:
                fc_value = norm_s1[g] / min_value
                decision = "s1"
            else:
                fc_value = min_value / norm_s2[g]
                decision = "s2"

            term.append(g)
            FC.append(fc_value)
            dec.append(decision)

        tmp = pd.DataFrame({"term": term, "FC": FC, "regulation": dec})
        tmp["type"] = "parent"

        # children check

        s1_tmp = pd.DataFrame(self.set_1["statistics"][sets])
        s2_tmp = pd.DataFrame(self.set_2["statistics"][sets])

        term = []
        norm_n = []

        for s1 in set(s1_tmp[children_columns]):

            term.append(s1)
            norm_n.append(
                float(np.mean(s1_tmp[children_n][s1_tmp[children_columns] == s1]))
                / self.s1_genes
            )

        s1 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        norm_n = []

        for s2 in set(s2_tmp[children_columns]):

            term.append(s2)
            norm_n.append(
                float(np.mean(s2_tmp[children_n][s2_tmp[children_columns] == s2]))
                / self.s2_genes
            )

        s2 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        FC = []
        dec = []

        terms_s1 = set(s1["term"])
        terms_s2 = set(s2["term"])

        norm_s1 = dict(zip(s1["term"], s1["norm_n"]))
        norm_s2 = dict(zip(s2["term"], s2["norm_n"]))

        all_terms = terms_s1.union(terms_s2)

        min_value = min(list(norm_s1.values()) + list(norm_s2.values())) / 10

        for g in all_terms:
            if g in terms_s1 and g in terms_s2:
                fc_value = norm_s1[g] / norm_s2[g]
                if fc_value >= self.min_fc:
                    decision = "s1"
                elif fc_value <= 1 / self.min_fc:
                    decision = "s2"
                else:
                    decision = "inter"
            elif g in terms_s1:
                fc_value = norm_s1[g] / min_value
                decision = "s1"
            else:
                fc_value = min_value / norm_s2[g]
                decision = "s2"

            term.append(g)
            FC.append(fc_value)
            dec.append(decision)

        tmp1 = pd.DataFrame({"term": term, "FC": FC, "regulation": dec})
        tmp1["type"] = "children"

        full_values = pd.concat([tmp, tmp1])

        self.GO = full_values

    def KEGG_diff(self):
        """
        This method performs a Differential Set Analysis (DSA) to compare two sets (set1 and set2) based on their KEGG enrichment analysis.

        Overview:
            This method assesses differences between set1 and set2 by calculating the normalized occurrence ('n_occ') of each term in both sets and determining the Fold Change (FC) between these occurrences.
            For term that is absent in one of sets, their normalized occurrence ('n_occ') is assigned a value equal to half the minimum 'n_occ' observed across all terms within the analysis type (e.g., GO-TERM, KEGG, etc.).
            By analyzing these FC values, the method identifies key differences in enrichment between the two sets, highlighting biologically significant pathways or terms unique or equal to each set.

        Formulas:
            The normalized occurrence ('n_occ') for each term is calculated as:
               n_occ = genes per term / total genes per set

            The Fold Change (FC) is then computed as the ratio of normalized occurrences:
               FC = set1 n_occ / set2 n_occ


        Interpretation:
           - If FC > self.min_fc, the term is considered more enriched in set1
           - If FC < 1/self.min_fc, the term is considered more enriched in set2
           - If FC < self.min_fc and > 1/self.min_fc, the term is equal between sets

        Returns:
            Updates `self.KEGG` with Reactome DSA data.
            To retrieve the results, use the `self.get_KEGG_diff` method.
        """

        # parent check

        parent_columns = "2nd"
        parent_n = "2nd_n"

        children_columns = "3rd"
        children_n = "3rd_n"

        sets = "KEGG"

        s1_tmp = pd.DataFrame(self.set_1["statistics"][sets])
        s2_tmp = pd.DataFrame(self.set_2["statistics"][sets])

        #######################################################################

        set_1_list = self.set_1["enrichment"]["gene_info"]["found_names"]
        set_2_list = self.set_2["enrichment"]["gene_info"]["found_names"]

        inter_tmp = pd.DataFrame(self.inter_terms[sets])

        inter_tmp = inter_tmp.explode("3rd_genes")
        inter_tmp = inter_tmp.explode("2nd_genes")

        inter_tmp["set_parent"] = None
        inter_tmp["set_children"] = None

        inter_tmp.loc[inter_tmp["3rd_genes"].isin(set_1_list), "set_children"] = "set1"
        inter_tmp.loc[inter_tmp["3rd_genes"].isin(set_2_list), "set_children"] = "set2"

        inter_tmp.loc[inter_tmp["2nd_genes"].isin(set_1_list), "set_parent"] = "set1"
        inter_tmp.loc[inter_tmp["2nd_genes"].isin(set_2_list), "set_parent"] = "set2"

        group_cols = ["2nd", "3rd", "set"]

        agg_dict = {
            "3rd_genes": lambda x: list(set(x)),
            "2nd_genes": lambda x: list(set(x)),
            "set_parent": lambda x: list(set(x)),
            "set_children": lambda x: list(set(x)),
            **{
                col: "first"
                for col in inter_tmp.columns
                if col
                not in group_cols
                + ["3rd_genes", "2nd_genes", "set_parent", "set_children"]
            },
        }

        inter_tmp = inter_tmp.groupby(group_cols, as_index=False).agg(agg_dict)

        inter_tmp["set"] = inter_tmp["set_parent"] + inter_tmp["set_children"]
        inter_tmp["set"] = [list(set(x)) for x in inter_tmp["set"]]
        inter_tmp = inter_tmp.explode("set_children")

        inter_tmp = inter_tmp[
            inter_tmp["set"].apply(lambda x: isinstance(x, (list, set)) and len(x) > 1)
        ]

        if len(inter_tmp) > 0:

            s1_tmp = pd.concat(
                [s1_tmp, inter_tmp[inter_tmp["set_children"] == "set1"]]
            ).reset_index(drop=True)

            s1_tmp = s1_tmp.drop(columns=["set_children", "set_parent", "set"])

            s2_tmp = pd.concat(
                [s2_tmp, inter_tmp[inter_tmp["set_children"] == "set2"]]
            ).reset_index(drop=True)

            s2_tmp = s2_tmp.drop(columns=["set_children", "set_parent", "set"])

            self.set_1["statistics"][sets] = s1_tmp.to_dict(orient="list")
            self.set_2["statistics"][sets] = s2_tmp.to_dict(orient="list")

        #######################################################################

        term = []
        norm_n = []

        for s1 in set(s1_tmp[parent_columns]):

            term.append(s1)
            norm_n.append(
                float(np.mean(s1_tmp[parent_n][s1_tmp[parent_columns] == s1]))
                / self.s1_genes
            )

        s1 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        norm_n = []

        for s2 in set(s2_tmp[parent_columns]):

            term.append(s2)
            norm_n.append(
                float(np.mean(s2_tmp[parent_n][s2_tmp[parent_columns] == s2]))
                / self.s2_genes
            )

        s2 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        FC = []
        dec = []

        terms_s1 = set(s1["term"])
        terms_s2 = set(s2["term"])

        norm_s1 = dict(zip(s1["term"], s1["norm_n"]))
        norm_s2 = dict(zip(s2["term"], s2["norm_n"]))

        all_terms = terms_s1.union(terms_s2)

        min_value = min(list(norm_s1.values()) + list(norm_s2.values())) / 10

        for g in all_terms:
            if g in terms_s1 and g in terms_s2:
                fc_value = norm_s1[g] / norm_s2[g]
                if fc_value >= self.min_fc:
                    decision = "s1"
                elif fc_value <= 1 / self.min_fc:
                    decision = "s2"
                else:
                    decision = "inter"
            elif g in terms_s1:
                fc_value = norm_s1[g] / min_value
                decision = "s1"
            else:
                fc_value = min_value / norm_s2[g]
                decision = "s2"

            term.append(g)
            FC.append(fc_value)
            dec.append(decision)

        tmp = pd.DataFrame({"term": term, "FC": FC, "regulation": dec})
        tmp["type"] = "parent"

        # children check

        s1_tmp = pd.DataFrame(self.set_1["statistics"][sets])
        s2_tmp = pd.DataFrame(self.set_2["statistics"][sets])

        term = []
        norm_n = []

        for s1 in set(s1_tmp[children_columns]):

            term.append(s1)
            norm_n.append(
                float(np.mean(s1_tmp[children_n][s1_tmp[children_columns] == s1]))
                / self.s1_genes
            )

        s1 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        norm_n = []

        for s2 in set(s2_tmp[children_columns]):

            term.append(s2)
            norm_n.append(
                float(np.mean(s2_tmp[children_n][s2_tmp[children_columns] == s2]))
                / self.s2_genes
            )

        s2 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        FC = []
        dec = []

        terms_s1 = set(s1["term"])
        terms_s2 = set(s2["term"])

        norm_s1 = dict(zip(s1["term"], s1["norm_n"]))
        norm_s2 = dict(zip(s2["term"], s2["norm_n"]))

        all_terms = terms_s1.union(terms_s2)

        min_value = min(list(norm_s1.values()) + list(norm_s2.values())) / 10

        for g in all_terms:
            if g in terms_s1 and g in terms_s2:
                fc_value = norm_s1[g] / norm_s2[g]
                if fc_value >= self.min_fc:
                    decision = "s1"
                elif fc_value <= 1 / self.min_fc:
                    decision = "s2"
                else:
                    decision = "inter"
            elif g in terms_s1:
                fc_value = norm_s1[g] / min_value
                decision = "s1"
            else:
                fc_value = min_value / norm_s2[g]
                decision = "s2"

            term.append(g)
            FC.append(fc_value)
            dec.append(decision)

        tmp1 = pd.DataFrame({"term": term, "FC": FC, "regulation": dec})
        tmp1["type"] = "children"

        full_values = pd.concat([tmp, tmp1])

        self.KEGG = full_values

    def REACTOME_diff(self):
        """
        This method performs a Differential Set Analysis (DSA) to compare two sets (set1 and set2) based on their Reactome enrichment analysis.

        Overview:
            This method assesses differences between set1 and set2 by calculating the normalized occurrence ('n_occ') of each term in both sets and determining the Fold Change (FC) between these occurrences.
            For term that is absent in one of sets, their normalized occurrence ('n_occ') is assigned a value equal to half the minimum 'n_occ' observed across all terms within the analysis type (e.g., GO-TERM, KEGG, etc.).
            By analyzing these FC values, the method identifies key differences in enrichment between the two sets, highlighting biologically significant pathways or terms unique or equal to each set.

        Formulas:
            The normalized occurrence ('n_occ') for each term is calculated as:
               n_occ = genes per term / total genes per set

            The Fold Change (FC) is then computed as the ratio of normalized occurrences:
               FC = set1 n_occ / set2 n_occ


        Interpretation:
           - If FC > self.min_fc, the term is considered more enriched in set1
           - If FC < 1/self.min_fc, the term is considered more enriched in set2
           - If FC < self.min_fc and > 1/self.min_fc, the term is equal between sets

        Returns:
            Updates `self.REACTOME` with Reactome DSA data.
            To retrieve the results, use the `self.get_REACTOME_diff` method.
        """

        # parent check

        parent_columns = "top_level_pathway"
        parent_n = "top_level_pathway_n"

        children_columns = "pathway"
        children_n = "pathway_n"

        sets = "REACTOME"

        s1_tmp = pd.DataFrame(self.set_1["statistics"][sets])
        s2_tmp = pd.DataFrame(self.set_2["statistics"][sets])

        #######################################################################

        set_1_list = self.set_1["enrichment"]["gene_info"]["found_names"]
        set_2_list = self.set_2["enrichment"]["gene_info"]["found_names"]

        inter_tmp = pd.DataFrame(self.inter_terms[sets])

        inter_tmp = inter_tmp.explode("pathway")
        inter_tmp = inter_tmp.explode("top_level_pathway")

        inter_tmp["set_parent"] = None
        inter_tmp["set_children"] = None

        inter_tmp.loc[inter_tmp["pathway_genes"].isin(set_1_list), "set_children"] = (
            "set1"
        )
        inter_tmp.loc[inter_tmp["pathway_genes"].isin(set_2_list), "set_children"] = (
            "set2"
        )

        inter_tmp.loc[
            inter_tmp["top_level_pathway_genes"].isin(set_1_list), "set_parent"
        ] = "set1"
        inter_tmp.loc[
            inter_tmp["top_level_pathway_genes"].isin(set_2_list), "set_parent"
        ] = "set2"

        group_cols = ["pathway", "top_level_pathway", "set"]

        agg_dict = {
            "pathway_genes": lambda x: list(set(x)),
            "top_level_pathway_genes": lambda x: list(set(x)),
            "set_parent": lambda x: list(set(x)),
            "set_children": lambda x: list(set(x)),
            **{
                col: "first"
                for col in inter_tmp.columns
                if col
                not in group_cols
                + [
                    "pathway_genes",
                    "top_level_pathway_genes",
                    "set_parent",
                    "set_children",
                ]
            },
        }

        inter_tmp = inter_tmp.groupby(group_cols, as_index=False).agg(agg_dict)

        inter_tmp["set"] = inter_tmp["set_parent"] + inter_tmp["set_children"]
        inter_tmp["set"] = [list(set(x)) for x in inter_tmp["set"]]
        inter_tmp = inter_tmp.explode("set_children")

        inter_tmp = inter_tmp[
            inter_tmp["set"].apply(lambda x: isinstance(x, (list, set)) and len(x) > 1)
        ]

        if len(inter_tmp) > 0:

            s1_tmp = pd.concat(
                [s1_tmp, inter_tmp[inter_tmp["set_children"] == "set1"]]
            ).reset_index(drop=True)

            s1_tmp = s1_tmp.drop(columns=["set_children", "set_parent", "set"])

            s2_tmp = pd.concat(
                [s2_tmp, inter_tmp[inter_tmp["set_children"] == "set2"]]
            ).reset_index(drop=True)

            s2_tmp = s2_tmp.drop(columns=["set_children", "set_parent", "set"])

            self.set_1["statistics"][sets] = s1_tmp.to_dict(orient="list")
            self.set_2["statistics"][sets] = s2_tmp.to_dict(orient="list")

        #######################################################################

        term = []
        norm_n = []

        for s1 in set(s1_tmp[parent_columns]):

            term.append(s1)
            norm_n.append(
                float(np.mean(s1_tmp[parent_n][s1_tmp[parent_columns] == s1]))
                / self.s1_genes
            )

        s1 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        norm_n = []

        for s2 in set(s2_tmp[parent_columns]):

            term.append(s2)
            norm_n.append(
                float(np.mean(s2_tmp[parent_n][s2_tmp[parent_columns] == s2]))
                / self.s2_genes
            )

        s2 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        FC = []
        dec = []

        terms_s1 = set(s1["term"])
        terms_s2 = set(s2["term"])

        norm_s1 = dict(zip(s1["term"], s1["norm_n"]))
        norm_s2 = dict(zip(s2["term"], s2["norm_n"]))

        all_terms = terms_s1.union(terms_s2)

        min_value = min(list(norm_s1.values()) + list(norm_s2.values())) / 10

        for g in all_terms:
            if g in terms_s1 and g in terms_s2:
                fc_value = norm_s1[g] / norm_s2[g]
                if fc_value >= self.min_fc:
                    decision = "s1"
                elif fc_value <= 1 / self.min_fc:
                    decision = "s2"
                else:
                    decision = "inter"
            elif g in terms_s1:
                fc_value = norm_s1[g] / min_value
                decision = "s1"
            else:
                fc_value = min_value / norm_s2[g]
                decision = "s2"

            term.append(g)
            FC.append(fc_value)
            dec.append(decision)

        tmp = pd.DataFrame({"term": term, "FC": FC, "regulation": dec})
        tmp["type"] = "parent"

        # children check

        s1_tmp = pd.DataFrame(self.set_1["statistics"][sets])
        s2_tmp = pd.DataFrame(self.set_2["statistics"][sets])

        term = []
        norm_n = []

        for s1 in set(s1_tmp[children_columns]):

            term.append(s1)
            norm_n.append(
                float(np.mean(s1_tmp[children_n][s1_tmp[children_columns] == s1]))
                / self.s1_genes
            )

        s1 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        norm_n = []

        for s2 in set(s2_tmp[children_columns]):

            term.append(s2)
            norm_n.append(
                float(np.mean(s2_tmp[children_n][s2_tmp[children_columns] == s2]))
                / self.s2_genes
            )

        s2 = pd.DataFrame({"term": term, "norm_n": norm_n})

        term = []
        FC = []
        dec = []

        terms_s1 = set(s1["term"])
        terms_s2 = set(s2["term"])

        norm_s1 = dict(zip(s1["term"], s1["norm_n"]))
        norm_s2 = dict(zip(s2["term"], s2["norm_n"]))

        all_terms = terms_s1.union(terms_s2)

        min_value = min(list(norm_s1.values()) + list(norm_s2.values())) / 10

        for g in all_terms:
            if g in terms_s1 and g in terms_s2:
                fc_value = norm_s1[g] / norm_s2[g]
                if fc_value >= self.min_fc:
                    decision = "self"
                elif fc_value <= 1 / self.min_fc:
                    decision = "s2"
                else:
                    decision = "inter"
            elif g in terms_s1:
                fc_value = norm_s1[g] / min_value
                decision = "s1"
            else:
                fc_value = min_value / norm_s2[g]
                decision = "s2"

            term.append(g)
            FC.append(fc_value)
            dec.append(decision)

        tmp1 = pd.DataFrame({"term": term, "FC": FC, "regulation": dec})
        tmp1["type"] = "children"

        full_values = pd.concat([tmp, tmp1])

        self.REACTOME = full_values

    def spec_diff(self):
        """
        This method performs a Differential Set Analysis (DSA) to compare two sets (set1 and set2) based on their specificity (HPA) enrichment analysis.

        Overview:
            This method assesses differences between set1 and set2 by calculating the normalized occurrence ('n_occ') of each term in both sets and determining the Fold Change (FC) between these occurrences.
            For term that is absent in one of sets, their normalized occurrence ('n_occ') is assigned a value equal to half the minimum 'n_occ' observed across all terms within the analysis type (e.g., GO-TERM, KEGG, etc.).
            By analyzing these FC values, the method identifies key differences in enrichment between the two sets, highlighting biologically significant pathways or terms unique or equal to each set.

        Formulas:
            The normalized occurrence ('n_occ') for each term is calculated as:
               n_occ = genes per term / total genes per set

            The Fold Change (FC) is then computed as the ratio of normalized occurrences:
               FC = set1 n_occ / set2 n_occ


        Interpretation:
           - If FC > self.min_fc, the term is considered more enriched in set1
           - If FC < 1/self.min_fc, the term is considered more enriched in set2
           - If FC < self.min_fc and > 1/self.min_fc, the term is equal between sets

        Returns:
            Updates `self.specificity` with specificity DSA data.
            To retrieve the results, use the `self.get_specificity_diff` method.
        """

        parent_columns = "specificity"
        parent_n = "n"

        sets = "specificity"

        key_list = self.set_1["statistics"][sets].keys()

        full_df = pd.DataFrame()

        for k in key_list:
            s1_tmp = pd.DataFrame(self.set_1["statistics"][sets][k])
            s2_tmp = pd.DataFrame(self.set_2["statistics"][sets][k])

            #######################################################################

            set_1_list = self.set_1["enrichment"]["gene_info"]["found_names"]
            set_2_list = self.set_2["enrichment"]["gene_info"]["found_names"]

            inter_tmp = pd.DataFrame(self.inter_terms[sets][k])

            inter_tmp = inter_tmp.explode("specificity")

            inter_tmp.loc[inter_tmp["genes"].isin(set_1_list), "set"] = "set1"
            inter_tmp.loc[inter_tmp["genes"].isin(set_2_list), "set"] = "set2"

            group_cols = ["specificity", "set"]

            agg_dict = {
                "genes": lambda x: list(set(x)),
                "set": lambda x: list(set(x)),
                **{
                    col: "first"
                    for col in inter_tmp.columns
                    if col not in group_cols + ["specificity", "set"]
                },
            }

            inter_tmp = inter_tmp.groupby(group_cols, as_index=False).agg(agg_dict)

            inter_tmp = inter_tmp.explode("set")

            inter_tmp = inter_tmp[
                inter_tmp["set"].apply(
                    lambda x: isinstance(x, (list, set)) and len(x) > 1
                )
            ]

            if len(inter_tmp) > 0:

                s1_tmp = pd.concat(
                    [s1_tmp, inter_tmp[inter_tmp["set_children"] == "set1"]]
                ).reset_index(drop=True)

                s1_tmp = s1_tmp.drop(columns=["set_children", "set_parent", "set"])

                s2_tmp = pd.concat(
                    [s2_tmp, inter_tmp[inter_tmp["set_children"] == "set2"]]
                ).reset_index(drop=True)

                s2_tmp = s2_tmp.drop(columns=["set_children", "set_parent", "set"])

                self.set_1["statistics"][sets][k] = s1_tmp.to_dict(orient="list")
                self.set_2["statistics"][sets][k] = s2_tmp.to_dict(orient="list")

            #######################################################################

            term = []
            norm_n = []

            for s1 in set(s1_tmp[parent_columns]):

                term.append(s1)
                norm_n.append(
                    float(np.mean(s1_tmp[parent_n][s1_tmp[parent_columns] == s1]))
                    / self.s1_genes
                )

            s1 = pd.DataFrame({"term": term, "norm_n": norm_n})

            term = []
            norm_n = []

            for s2 in set(s2_tmp[parent_columns]):

                term.append(s2)
                norm_n.append(
                    float(np.mean(s2_tmp[parent_n][s2_tmp[parent_columns] == s2]))
                    / self.s2_genes
                )

            s2 = pd.DataFrame({"term": term, "norm_n": norm_n})

            term = []
            FC = []
            dec = []

            terms_s1 = set(s1["term"])
            terms_s2 = set(s2["term"])

            norm_s1 = dict(zip(s1["term"], s1["norm_n"]))
            norm_s2 = dict(zip(s2["term"], s2["norm_n"]))

            all_terms = terms_s1.union(terms_s2)

            min_value = min(list(norm_s1.values()) + list(norm_s2.values())) / 10

            for g in all_terms:
                if g in terms_s1 and g in terms_s2:
                    fc_value = norm_s1[g] / norm_s2[g]
                    if fc_value >= self.min_fc:
                        decision = "s1"
                    elif fc_value <= 1 / self.min_fc:
                        decision = "s2"
                    else:
                        decision = "inter"
                elif g in terms_s1:
                    fc_value = norm_s1[g] / min_value
                    decision = "s1"
                else:
                    fc_value = min_value / norm_s2[g]
                    decision = "s2"

                term.append(g)
                FC.append(fc_value)
                dec.append(decision)

            tmp = pd.DataFrame({"term": term, "FC": FC, "regulation": dec})
            tmp["set"] = k

            full_df = pd.concat([full_df, tmp])

        self.specificity = full_df

    def gi_diff(self):
        """
        This method performs a Differential Set Analysis (DSA) to compare two sets (set1 and set2) based on their Genes Interactions (GI) enrichment analysis.

        Overview:
            This method assesses differences between set1 and set2 by identifying gene/protein interactions that occur between set1 and set2, but were not found independently in either set1 or set2.

        Returns:
            Updates `self.GI` with Reactome DSA data.
            To retrieve the results, use the `self.get_GI_diff` method.
        """

        full_ans = pd.DataFrame(self.features_interactions_statistics)

        s1_ans = pd.DataFrame(self.set_1["statistics"]["interactions"])
        s2_ans = pd.DataFrame(self.set_2["statistics"]["interactions"])

        full_ans["set"] = "inter"

        full_ans["set"][
            full_ans["A"].isin(list(s1_ans["A"]))
            & full_ans["B"].isin(list(s1_ans["B"]))
        ] = "s1"
        full_ans["set"][
            full_ans["A"].isin(list(s2_ans["A"]))
            & full_ans["B"].isin(list(s2_ans["B"]))
        ] = "s2"

        self.GI = full_ans

    def network_diff(self):
        """
        This method performs a Differential Set Analysis (DSA) to compare two sets (set1 and set2) based on their network of GO-TERM, KEGG, and Reactome network analysis.

        Overview:
            This method assesses differences between set1 and set2 by identifying gene/protein occurrences that are enriched in the combined data of set1 and set2, but are not present independently in either set1 or set2.

        Returns:
            Updates `self.networks` with network DSA data.
            To retrieve the results, use the `self.get_networks_diff` method.
        """

        networks = {}

        kn = pd.DataFrame(self.KEGG_net)

        s1_ans = pd.DataFrame(self.set_1["networks"]["KEGG"])
        s2_ans = pd.DataFrame(self.set_2["networks"]["KEGG"])

        kn["set"] = "inter"

        kn["set"][
            kn["parent"].isin(list(s1_ans["parent"]))
            & kn["children"].isin(list(s1_ans["children"]))
        ] = "s1"
        kn["set"][
            kn["parent"].isin(list(s2_ans["parent"]))
            & kn["children"].isin(list(s2_ans["children"]))
        ] = "s2"

        s1_ans = s1_ans[
            ~s1_ans["parent"].isin(list(kn["parent"]))
            & ~s1_ans["children"].isin(list(kn["children"]))
        ]

        s1_ans["set"] = "s1"

        s2_ans = s2_ans[
            ~s2_ans["parent"].isin(list(kn["parent"]))
            & ~s2_ans["children"].isin(list(kn["children"]))
        ]

        s2_ans["set"] = "s2"

        kn = pd.concat([kn, s1_ans, s2_ans])

        networks["KEGG"] = kn.to_dict(orient="list")

        kn = pd.DataFrame(self.REACTOME_net)

        s1_ans = pd.DataFrame(self.set_1["networks"]["REACTOME"])
        s2_ans = pd.DataFrame(self.set_2["networks"]["REACTOME"])

        kn["set"] = "inter"

        kn["set"][
            kn["parent"].isin(list(s1_ans["parent"]))
            & kn["children"].isin(list(s1_ans["children"]))
        ] = "s1"
        kn["set"][
            kn["parent"].isin(list(s2_ans["parent"]))
            & kn["children"].isin(list(s2_ans["children"]))
        ] = "s2"

        s1_ans = s1_ans[
            ~s1_ans["parent"].isin(list(kn["parent"]))
            & ~s1_ans["children"].isin(list(kn["children"]))
        ]

        s1_ans["set"] = "s1"

        s2_ans = s2_ans[
            ~s2_ans["parent"].isin(list(kn["parent"]))
            & ~s2_ans["children"].isin(list(kn["children"]))
        ]

        s2_ans["set"] = "s2"

        kn = pd.concat([kn, s1_ans, s2_ans])

        networks["REACTOME"] = kn.to_dict(orient="list")

        kn = pd.DataFrame(self.GO_net)

        s1_ans = pd.DataFrame(self.set_1["networks"]["GO-TERM"])
        s2_ans = pd.DataFrame(self.set_2["networks"]["GO-TERM"])

        kn["set"] = "inter"

        kn["set"][
            kn["parent"].isin(list(s1_ans["parent"]))
            & kn["children"].isin(list(s1_ans["children"]))
        ] = "s1"
        kn["set"][
            kn["parent"].isin(list(s2_ans["parent"]))
            & kn["children"].isin(list(s2_ans["children"]))
        ] = "s2"

        s1_ans = s1_ans[
            ~s1_ans["parent"].isin(list(kn["parent"]))
            & ~s1_ans["children"].isin(list(kn["children"]))
        ]

        s1_ans["set"] = "s1"

        s2_ans = s2_ans[
            ~s2_ans["parent"].isin(list(kn["parent"]))
            & ~s2_ans["children"].isin(list(kn["children"]))
        ]

        s2_ans["set"] = "s2"

        kn = pd.concat([kn, s1_ans, s2_ans])

        networks["GO-TERM"] = kn.to_dict(orient="list")

        self.networks = networks

    def inter_processes(self):
        """
        This method performs Differential Set Analysis (DSA) to compare two datasets (set1 and set2).
        It identifies new terms or pathways in the combined set1 and set2 data, enabling enrichment analysis and presenting inter terms for:
            - GO-TERM
            - KEGG
            - Reactome
            - specificity (HPA)

        Returns:
            Updates `self.inter_terms` with Inter Terms DSA data.
            To retrieve the results, use the `self.get_inter_terms` method.
        """

        s1_genes = self.set_1["enrichment"]["gene_info"]["found_names"]
        s2_genes = self.set_2["enrichment"]["gene_info"]["found_names"]

        inter_terms = {}

        # GO
        tmp = pd.DataFrame(self.GO_over)

        s1_ans = pd.DataFrame(self.set_1["statistics"]["GO-TERM"])
        s2_ans = pd.DataFrame(self.set_2["statistics"]["GO-TERM"])

        tmp["set"] = "inter"

        tmp["set"][
            tmp["parent"].isin(list(s1_ans["parent"]))
            & tmp["child"].isin(list(s1_ans["child"]))
        ] = "s1"
        tmp["set"][
            tmp["parent"].isin(list(s2_ans["parent"]))
            & tmp["child"].isin(list(s2_ans["child"]))
        ] = "s2"

        tmp = tmp[tmp["set"] == "inter"]

        drop = []
        for i in tmp.index:
            tmp_names = tmp["parent_genes"][i] + tmp["child_genes"][i]
            if any(name not in s1_genes and name not in s2_genes for name in tmp_names):
                drop.append(i)

        tmp = tmp.drop(drop, axis=0)

        inter_terms["GO-TERM"] = tmp.to_dict(orient="list")

        # KEGG
        tmp = pd.DataFrame(self.KEGG_over)

        s1_ans = pd.DataFrame(self.set_1["statistics"]["KEGG"])
        s2_ans = pd.DataFrame(self.set_2["statistics"]["KEGG"])

        tmp["set"] = "inter"

        tmp["set"][
            tmp["2nd"].isin(list(s1_ans["2nd"])) & tmp["3rd"].isin(list(s1_ans["3rd"]))
        ] = "s1"
        tmp["set"][
            tmp["2nd"].isin(list(s2_ans["2nd"])) & tmp["3rd"].isin(list(s2_ans["3rd"]))
        ] = "s2"

        tmp = tmp[tmp["set"] == "inter"]

        drop = []
        for i in tmp.index:
            tmp_names = tmp["2nd_genes"][i] + tmp["3rd_genes"][i]
            if any(name not in s1_genes and name not in s2_genes for name in tmp_names):
                drop.append(i)

        tmp = tmp.drop(drop, axis=0)

        inter_terms["KEGG"] = tmp.to_dict(orient="list")

        # REACTOME
        tmp = pd.DataFrame(self.REACTOME_over)

        s1_ans = pd.DataFrame(self.set_1["statistics"]["REACTOME"])
        s2_ans = pd.DataFrame(self.set_2["statistics"]["REACTOME"])

        tmp["set"] = "inter"

        tmp["set"][
            tmp["top_level_pathway"].isin(list(s1_ans["top_level_pathway"]))
            & tmp["pathway"].isin(list(s1_ans["pathway"]))
        ] = "s1"
        tmp["set"][
            tmp["top_level_pathway"].isin(list(s2_ans["top_level_pathway"]))
            & tmp["pathway"].isin(list(s2_ans["pathway"]))
        ] = "s2"

        tmp = tmp[tmp["set"] == "inter"]

        drop = []
        for i in tmp.index:
            tmp_names = tmp["pathway_genes"][i] + tmp["top_level_pathway_genes"][i]
            if any(name not in s1_genes and name not in s2_genes for name in tmp_names):
                drop.append(i)

        tmp = tmp.drop(drop, axis=0)

        inter_terms["REACTOME"] = tmp.to_dict(orient="list")

        # spec
        tmp = pd.DataFrame(self.spec_over)

        key_list = self.set_1["statistics"]["specificity"].keys()

        spec_dict = {}
        for k in key_list:

            tmp = pd.DataFrame(self.spec_over[k])

            s1_ans = pd.DataFrame(self.set_1["statistics"]["specificity"][k])
            s2_ans = pd.DataFrame(self.set_2["statistics"]["specificity"][k])

            tmp["set"] = "inter"

            tmp["set"][tmp["specificity"].isin(list(s1_ans["specificity"]))] = "s1"
            tmp["set"][tmp["specificity"].isin(list(s2_ans["specificity"]))] = "s2"

            tmp = tmp[tmp["set"] == "inter"]

            drop = []
            for i in tmp.index:
                tmp_names = tmp["pathway_genes"][i] + tmp["top_level_pathway_genes"][i]
                if any(
                    name not in s1_genes and name not in s2_genes for name in tmp_names
                ):
                    drop.append(i)

            tmp = tmp.drop(drop, axis=0)

            spec_dict[k] = tmp.to_dict(orient="list")

        inter_terms["specificity"] = spec_dict

        self.inter_terms = inter_terms

    def connections_diff(self):
        """
        This method selects elements from the GEDS database that are included in the CellPhone/CellTalk (CellConnections) information for two sets of features.

        It allows the identification of ligand-to-receptor connections, including:
            * set1 -> set2
            * set2 -> set1

        Returns:
            Updates `self.lr_con_set1_set2` and `self.lr_con_set2_set1` with CellPhone / CellTalk information.
            To retrieve the results, use the `self.get_set_to_set_con` method.
        """

        s1_genes = pd.DataFrame(self.set_1["enrichment"]["gene_info"])
        s2_genes = pd.DataFrame(self.set_2["enrichment"]["gene_info"])

        conn = sqlite3.connect(os.path.join(self.path_in_inside, "GEDS_db.db"))

        species = self.set_1["enrichment"]["species"]["species_study"]
        species = ", ".join(map(lambda x: f"'{x}'", species))

        ids1 = [int(x) for x in s1_genes["id_cell_int"] if x == x]
        ids2 = [int(x) for x in s2_genes["id_cell_int"] if x == x]

        # set1

        query = f"""
        SELECT * 
        FROM CellInteractions 
        WHERE protein_id_1 IN ({', '.join(map(str, ids1))}) 
          AND protein_id_2 IN ({', '.join(map(str, ids2))})
          AND Species IN ({species});
        """

        df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

        df = pd.merge(
            df,
            s1_genes[["id_cell_int", "found_names"]],
            how="left",
            left_on="protein_id_1",
            right_on="id_cell_int",
        )
        df = df.drop(["id_cell_int"], axis=1)
        df = df.rename(columns={"found_names": "found_names_1"})

        df = pd.merge(
            df,
            s2_genes[["id_cell_int", "found_names"]],
            how="left",
            left_on="protein_id_2",
            right_on="id_cell_int",
        )
        df = df.drop(["id_cell_int"], axis=1)
        df = df.rename(columns={"found_names": "found_names_2"})

        self.lr_con_set1_set2 = df.to_dict(orient="list")

        del df

        # set2

        query = f"""
        SELECT * 
        FROM CellInteractions 
        WHERE protein_id_1 IN ({', '.join(map(str, ids2))}) 
          AND protein_id_2 IN ({', '.join(map(str, ids1))})
          AND Species IN ({species});
        """

        df = pd.read_sql_query(query, conn).applymap(self.deserialize_data)

        df = pd.merge(
            df,
            s2_genes[["id_cell_int", "found_names"]],
            how="left",
            left_on="protein_id_1",
            right_on="id_cell_int",
        )
        df = df.drop(["id_cell_int"], axis=1)
        df = df.rename(columns={"found_names": "found_names_1"})

        df = pd.merge(
            df,
            s1_genes[["id_cell_int", "found_names"]],
            how="left",
            left_on="protein_id_2",
            right_on="id_cell_int",
        )
        df = df.drop(["id_cell_int"], axis=1)
        df = df.rename(columns={"found_names": "found_names_2"})

        self.lr_con_set2_set1 = df.to_dict(orient="list")

        del df

    def full_analysis(self):
        """
         This method performs a full Differential Set Analysis (DSA) to compare two sets (set1 and set2) based on:

            - Human Protein Atlas (HPA) [see self.spec_diff() method]
            - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see self.KEGG_diff() method]
            - GeneOntology (GO-TERM) [see self.GO_diff() method]
            - Reactome [see self.REACTOME_diff() method]
            - Inter Terms (IT) [see self.gi_diff() method]
            - Genes Interactions (GI) [see self.gi_diff() method]
            - Inter CellConnections (ICC) [see self.connections_diff() method]
            - Networks (GO-TERM, KEGG, Reactome) [see self.network_diff() method]

        Returns:
            To retrieve the results, use the `self.get_results` method.
        """

        print("\nGO-TERM differential analysis...")

        self.GO_diff()

        print("\nKEGG differential analysis...")

        self.KEGG_diff()

        print("\nREACTOME differential analysis...")

        self.REACTOME_diff()

        print("\nSpecificity differential analysis...")

        self.spec_diff()

        print("\nGene Interactions (GI) differential analysis...")

        self.gi_diff()

        print("\nNetworks differential analysis...")

        self.network_diff()

        print("\nInter Terms (IT) searching...")

        print("\nInter CellConnections (ICC) searching...")

        self.connections_diff()

    def get_results(self):
        """
        This method returns the full analysis dictionary containing on keys:
            * 'GI' - Genes Interactions (STRING / IntAct) [see `self.get_GI_diff` property]
            * 'inter_cell_connections' - Inter CellConnections (CellTalk / CellPhone) [see `self.get_set_to_set_con` property]
            * 'inter_terms' - Inter Terms (KEGG, REACTOME, GO-TERM) [see `self.get_networks_diff` property]
            * 'networks' - Network data [see `self.get_inter_terms` property]:
                - 'KEGG' - Kyoto Encyclopedia of Genes and Genomes (KEGG)
                - 'GO-TERM' - GeneOntology (GO-TERM)
                - 'REACTOME' - Reactome
            * 'regulations' - Terms / Pathways:
                - 'specificity' - Human Protein Atlas (HPA) [see 'self.get_specificity_diff' property]
                - 'KEGG' - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see 'self.get_KEGG_diff' property]
                - 'GO-TERM' - GeneOntology (GO-TERM) [see 'self.get_GO_diff' property]
                - 'REACTOME' - Reactome [see 'self.get_REACTOME_diff' property]
            * 'set1' - input dictionary with results of enrichment and statistical analysis for set1
            * 'set2' - input dictionary with results of enrichment and statistical analysis for set2


            Returns:
                dict (dict) - full analysis data
        """

        results = {}

        results["set_1"] = self.set_1
        results["set_2"] = self.set_2

        results["regulations"] = {}

        results["regulations"]["GO-TERM"] = self.get_GO_diff()

        results["regulations"]["KEGG"] = self.get_KEGG_diff()

        results["regulations"]["REACTOME"] = self.get_REACTOME_diff()

        results["regulations"]["specificity"] = self.get_specificity_diff()

        results["GI"] = self.get_GI_diff()

        results["networks"] = self.get_networks_diff()

        results["inter_terms"] = self.get_inter_terms()

        results["inter_cell_conections"] = self.get_set_to_set_con()

        return results


class VisualizationDES(Visualization):

    def __init__(self, input_data: dict):

        self.input_data = input_data
        self.show_plot = False
        self.parent_stats = False

    ###########################################################################
    # Single set analysis visualization

    def set_gene_type_plot(
        self, set_num: int = 1, cmap="summer", image_width=6, image_high=6, font_size=15
    ):

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        tmp_info = self.input_data[f"set_{set_num}"]["enrichment"]["gene_info"]

        sp = self.input_data[f"set_{set_num}"]["enrichment"]["species"]["species_genes"]

        h_genes = []
        m_genes = []
        r_genes = []

        if "Homo sapiens" in sp:

            h_genes = tmp_info["gen_type_Homo_sapiens"]

        if "Mus musculus" in sp:

            m_genes = tmp_info["gen_type_Mus_musculus"]

        if "Rattus norvegicus" in sp:

            r_genes = tmp_info["gen_type_Rattus_norvegicus"]

        full_genes = []
        for i in range(len(tmp_info["sid"])):
            g = []

            if len(h_genes) > 0:
                if isinstance(h_genes[i], list):
                    g += h_genes[i]
                elif h_genes[i] is None:
                    g += []
                else:
                    g.append(h_genes[i])

            if len(m_genes) > 0:
                if isinstance(m_genes[i], list):
                    g += m_genes[i]
                elif m_genes[i] is None:
                    g += []
                else:
                    g.append(m_genes[i])

            if len(r_genes) > 0:
                if isinstance(r_genes[i], list):
                    g += r_genes[i]
                elif r_genes[i] is None:
                    g += []
                else:
                    g.append(r_genes[i])

            if len(g) == 0:
                g = ["undefined"]

            full_genes += list(set(g))

        count_gene = Counter(full_genes)

        count_gene = pd.DataFrame(count_gene.items(), columns=["gene_type", "n"])

        count_gene["pct"] = (count_gene["n"] / sum(count_gene["n"])) * 100

        count_gene["pct"] = [round(x, 2) for x in count_gene["pct"]]

        count_gene = count_gene.sort_values("n", ascending=False)

        count_gene = count_gene.reset_index(drop=True)

        labels = (
            count_gene["gene_type"]
            + [" : "] * len(count_gene["gene_type"])
            + count_gene["pct"].astype(str)
            + ["%"] * len(count_gene["gene_type"])
        )

        cn = len(count_gene["gene_type"])

        existing_cmap = plt.get_cmap(cmap)

        colors = [existing_cmap(i / cn) for i in range(cn)]

        colordf = pd.DataFrame({"color": colors, "label": labels})

        fig, ax = plt.subplots(
            figsize=(image_width, image_high), subplot_kw=dict(aspect="equal")
        )

        wedges, texts = ax.pie(
            count_gene["pct"],
            startangle=90,
            labeldistance=1.05,
            colors=[
                colordf["color"][colordf["label"] == x][
                    colordf.index[colordf["label"] == x][0]
                ]
                for x in labels
            ],
            wedgeprops={"linewidth": 0.5, "edgecolor": "black"},
        )

        kw = dict(arrowprops=dict(arrowstyle="-"), zorder=0, va="center")
        n = 0
        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            if len(labels[i]) > 0:
                n += 0.45
                ax.annotate(
                    labels[i],
                    xy=(x, y),
                    xytext=(1.4 * x + (n * x / 4), y * 1.1 + (n * y / 4)),
                    horizontalalignment=horizontalalignment,
                    fontsize=font_size,
                    weight="bold",
                    **kw,
                )

        circle2 = plt.Circle((0, 0), 0.6, color="white")
        circle2.set_edgecolor("black")

        ax.text(
            0.5,
            0.5,
            "Gene type",
            transform=ax.transAxes,
            va="center",
            ha="center",
            backgroundcolor="white",
            weight="bold",
            fontsize=int(font_size * 1.25),
        )

        p = plt.gcf()
        p.gca().add_artist(circle2)

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def set_GO_plot(
        self,
        set_num=1,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n=25,
        min_terms: int = 5,
        selected_parent: list = [],
        side="right",
        color="blue",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):

        sets = "GO-TERM"
        column = "child_name"

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        test_string = self.select_test(test, adj)

        tmp_in = pd.DataFrame(self.input_data[f"set_{set_num}"]["statistics"][sets])

        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"parent_{test_string}"] <= p_val]

        tmp_in = tmp_in[tmp_in[f"child_{test_string}"] <= p_val]
        tmp_in[f"child_{test_string}"] = (
            tmp_in[f"child_{test_string}"]
            + np.min(
                tmp_in[f"child_{test_string}"][tmp_in[f"child_{test_string}"] != 0]
            )
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"child_{test_string}"])
        tmp_in = tmp_in.reset_index(drop=True)

        if stat.upper() == "perc".upper():
            x_max = np.max(tmp_in["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(tmp_in["-log(p-val)"])

        else:
            x_max = np.max(tmp_in["n"])

        iter_set = list(set(tmp_in["parent_name"]))

        if len(selected_parent) > 0:
            tmp_iter = []
            for i in selected_parent:
                if i in iter_set:
                    tmp_iter.append(i)
                else:
                    print(f"\nParent term name: {i} was not found")

            iter_set = tmp_iter

            if len(iter_set) == 0:
                raise ValueError("Nothing to return")

        hlist = []

        valid_iter_set = []

        for l, it in enumerate(iter_set):

            inx = [x for x in tmp_in.index if it in tmp_in["parent_name"][x]]
            tmp = tmp_in.loc[inx]

            if len(set(tmp[column])) >= min_terms:
                valid_iter_set.append(it)

                if float(len(set(tmp[column]))) > n:

                    tn = n
                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / 2.1)

                else:

                    tn = float(len(set(tmp[column])))

                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))

                    else:
                        hlist.append(tn / 2.1)

        iter_set = valid_iter_set

        fig = plt.figure(figsize=(width, sum(hlist)))

        gs = GridSpec(len(hlist), 1, height_ratios=hlist)

        gs.update(hspace=len(hlist) / 50)

        for l, i in enumerate(iter_set):
            inx = [x for x in tmp_in.index if i in tmp_in["parent_name"][x]]
            tmp = tmp_in.loc[inx]

            ax = fig.add_subplot(gs[l])

            show_axis = l + 1 == len(iter_set)

            self.bar_plot(
                data=tmp,
                n=n,
                side=side,
                color="blue",
                width=width,
                bar_width=bar_width,
                stat=stat,
                sets="GO-TERM",
                column=column,
                x_max=x_max,
                show_axis=show_axis,
                title=i,
                ax=ax,
            )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def set_KEGG_plot(
        self,
        set_num=1,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n=5,
        min_terms: int = 5,
        selected_parent: list = [],
        side="right",
        color="orange",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):

        sets = "KEGG"
        column = "3rd"

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        test_string = self.select_test(test, adj)

        tmp_in = pd.DataFrame(self.input_data[f"set_{set_num}"]["statistics"][sets])
        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"2nd_{test_string}"] <= p_val]
        tmp_in = tmp_in[tmp_in[f"3rd_{test_string}"] <= p_val]
        tmp_in[f"3rd_{test_string}"] = (
            tmp_in[f"3rd_{test_string}"]
            + np.min(tmp_in[f"3rd_{test_string}"][tmp_in[f"3rd_{test_string}"] != 0])
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"3rd_{test_string}"])
        tmp_in = tmp_in.reset_index(drop=True)

        if stat.upper() == "perc".upper():
            x_max = np.max(tmp_in["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(tmp_in["-log(p-val)"])

        else:
            x_max = np.max(tmp_in["n"])

        # queue

        tmp_qq = tmp_in[["2nd", "-log(p-val)"]]

        tmp_qq["amount"] = tmp_qq["2nd"].map(tmp_qq["2nd"].value_counts())

        tmp_qq = tmp_qq.groupby("2nd", as_index=False).agg(
            amount=("amount", "first"), avg_log_pval=("-log(p-val)", "mean")
        )

        tmp_qq = tmp_qq.sort_values(
            by=["amount", "avg_log_pval"], ascending=[False, False]
        ).reset_index(drop=True)

        #######################################################################
        iter_set = list(tmp_qq["2nd"])

        if len(selected_parent) > 0:
            tmp_iter = []
            for i in selected_parent:
                if i in iter_set:
                    tmp_iter.append(i)
                else:
                    print(f"\nParent term name: {i} was not found")

            iter_set = tmp_iter

            if len(iter_set) == 0:
                raise ValueError("Nothing to return")

        hlist = []

        valid_iter_set = []

        for l, it in enumerate(iter_set):

            inx = [x for x in tmp_in.index if it in tmp_in["2nd"][x]]
            tmp = tmp_in.loc[inx]

            if len(set(tmp[column])) >= min_terms:
                valid_iter_set.append(i)

                if float(len(set(tmp[column]))) > n:

                    tn = n
                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / 2.1)

                else:

                    tn = float(len(set(tmp[column])))

                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))

                    else:
                        hlist.append(tn / 2.1)

        iter_set = valid_iter_set

        fig = plt.figure(figsize=(width, sum(hlist)))

        gs = GridSpec(len(hlist), 1, height_ratios=hlist)
        gs.update(hspace=len(hlist) / 50)

        for l, i in enumerate(iter_set):
            inx = [x for x in tmp_in.index if i in tmp_in["2nd"][x]]
            tmp = tmp_in.loc[inx]

            ax = fig.add_subplot(gs[l])

            show_axis = l + 1 == len(iter_set)

            self.bar_plot(
                data=tmp,
                n=n,
                side=side,
                color=color,
                width=width,
                bar_width=bar_width,
                stat=stat,
                sets="KEGG",
                column=column,
                x_max=x_max,
                show_axis=show_axis,
                title=i,
                ax=ax,
            )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def set_REACTOME_plot(
        self,
        set_num=1,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n: int = 5,
        min_terms: int = 5,
        selected_parent: list = [],
        side="right",
        color="silver",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):

        sets = "REACTOME"
        column = "pathway"

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        test_string = self.select_test(test, adj)

        tmp_in = pd.DataFrame(self.input_data[f"set_{set_num}"]["statistics"][sets])
        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"top_level_pathway_{test_string}"] <= p_val]
        tmp_in = tmp_in[tmp_in[f"pathway_{test_string}"] <= p_val]
        tmp_in[f"pathway_{test_string}"] = (
            tmp_in[f"pathway_{test_string}"]
            + np.min(
                tmp_in[f"pathway_{test_string}"][tmp_in[f"pathway_{test_string}"] != 0]
            )
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"pathway_{test_string}"])
        tmp_in = tmp_in.reset_index(drop=True)

        if stat.upper() == "perc".upper():
            x_max = np.max(tmp_in["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(tmp_in["-log(p-val)"])

        else:
            x_max = np.max(tmp_in["n"])

        # queue

        tmp_qq = tmp_in[["top_level_pathway", "-log(p-val)"]]

        tmp_qq["amount"] = tmp_qq["top_level_pathway"].map(
            tmp_qq["top_level_pathway"].value_counts()
        )

        tmp_qq = tmp_qq.groupby("top_level_pathway", as_index=False).agg(
            amount=("amount", "first"), avg_log_pval=("-log(p-val)", "mean")
        )

        tmp_qq = tmp_qq.sort_values(
            by=["amount", "avg_log_pval"], ascending=[False, False]
        ).reset_index(drop=True)

        #######################################################################
        iter_set = list(tmp_qq["top_level_pathway"])

        if len(selected_parent) > 0:
            tmp_iter = []
            for i in selected_parent:
                if i in iter_set:
                    tmp_iter.append(i)
                else:
                    print(f"\nParent term name: {i} was not found")

            iter_set = tmp_iter

            if len(iter_set) == 0:
                raise ValueError("Nothing to return")

        hlist = []

        valid_iter_set = []

        for l, it in enumerate(iter_set):

            inx = [x for x in tmp_in.index if it in tmp_in["top_level_pathway"][x]]
            tmp = tmp_in.loc[inx]

            if len(set(tmp[column])) >= min_terms:
                valid_iter_set.append(i)

                if float(len(set(tmp[column]))) > n:

                    tn = n
                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / 2.1)

                else:

                    tn = float(len(set(tmp[column])))

                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))

                    else:
                        hlist.append(tn / 2.1)

        iter_set = valid_iter_set

        fig = plt.figure(figsize=(width, sum(hlist)))

        gs = GridSpec(len(hlist), 1, height_ratios=hlist)
        gs.update(hspace=len(hlist) / 50)

        for l, i in enumerate(iter_set):
            inx = [x for x in tmp_in.index if i in tmp_in["top_level_pathway"][x]]
            tmp = tmp_in.loc[inx]

            ax = fig.add_subplot(gs[l])

            show_axis = l + 1 == len(iter_set)

            self.bar_plot(
                data=tmp,
                n=n,
                side=side,
                color=color,
                width=width,
                bar_width=bar_width,
                stat=stat,
                sets="REACTOME",
                column=column,
                x_max=x_max,
                show_axis=show_axis,
                title=i,
                ax=ax,
            )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def set_SPECIFICITY_plot(
        self,
        set_num=1,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n=5,
        side="right",
        color="bisque",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):

        sets = "specificity"
        column = "specificity"

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        test_string = self.select_test(test, adj)

        full_df = pd.DataFrame()

        for si in self.input_data[f"set_{set_num}"]["statistics"][sets].keys():

            tmp_in = pd.DataFrame(
                self.input_data[f"set_{set_num}"]["statistics"][sets][si]
            )

            tmp_in = tmp_in[tmp_in[test_string] <= p_val]
            tmp_in[test_string] = (
                tmp_in[test_string]
                + np.min(tmp_in[test_string][tmp_in[test_string] != 0]) / 2
            )
            tmp_in["-log(p-val)"] = -np.log(tmp_in[test_string])
            tmp_in = tmp_in.reset_index(drop=True)
            tmp_in["set"] = si

            full_df = pd.concat([full_df, tmp_in])

        full_df = full_df.reset_index(drop=True)
        full_df["specificity"] = [
            x[0].upper() + x[1:] if isinstance(x, str) and len(x) > 0 else x
            for x in full_df["specificity"]
        ]

        if stat.upper() == "perc".upper():
            x_max = np.max(full_df["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(full_df["-log(p-val)"])

        else:
            x_max = np.max(full_df["n"])

        # queue

        tmp_qq = full_df[["set", "-log(p-val)"]]

        tmp_qq["amount"] = tmp_qq["set"].map(tmp_qq["set"].value_counts())

        tmp_qq = tmp_qq.groupby("set", as_index=False).agg(
            amount=("amount", "first"), avg_log_pval=("-log(p-val)", "mean")
        )

        tmp_qq = tmp_qq.sort_values(
            by=["amount", "avg_log_pval"], ascending=[False, False]
        ).reset_index(drop=True)

        #######################################################################
        iter_set = list(tmp_qq["set"])
        # colors = ['darkblue', 'blue', 'lightblue']

        hlist = []
        for it in iter_set:
            print(it)
            inx = [x for x in full_df.index if it in full_df["set"][x]]
            tmp = full_df.loc[inx]
            if float(len(tmp[column])) > n:
                tn = n
                if tn < 6:
                    if tn < 2:
                        hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / (2.12 + ((6 - tn) / 10)))
                else:
                    hlist.append(tn / 2.1)

            else:
                tn = float(len(tmp[column]))
                if tn < 6:
                    if tn < 2:
                        hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / (2.12 + ((6 - tn) / 10)))

                else:
                    hlist.append(tn / 2.1)

        fig = plt.figure(figsize=(width, sum(hlist)))

        gs = GridSpec(len(hlist), 1, height_ratios=hlist)
        gs.update(hspace=len(hlist) / 50)

        for l, i in enumerate(iter_set):
            inx = [x for x in full_df.index if i in full_df["set"][x]]
            tmp = full_df.loc[inx]

            ax = fig.add_subplot(gs[l])

            show_axis = l + 1 == len(iter_set)

            self.bar_plot(
                data=tmp,
                n=n,
                side=side,
                color=color,
                width=width,
                bar_width=bar_width,
                stat=stat,
                sets="specificity",
                column=column,
                x_max=x_max,
                show_axis=show_axis,
                title=i,
                ax=ax,
            )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def set_DISEASES_plot(
        self,
        set_num=1,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n=5,
        side="right",
        color="thistle",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):

        sets = "DISEASES"
        column = "disease"

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        test_string = self.select_test(test, adj)

        tmp_in = pd.DataFrame(self.input_data[f"set_{set_num}"]["statistics"][sets])

        tmp_in = tmp_in[tmp_in[test_string] <= p_val]
        tmp_in[test_string] = (
            tmp_in[test_string]
            + np.min(tmp_in[test_string][tmp_in[test_string] != 0]) / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[test_string])
        tmp_in = tmp_in.reset_index(drop=True)
        tmp_in["disease"] = [
            x[0].upper() + x[1:] if isinstance(x, str) and len(x) > 0 else x
            for x in tmp_in["disease"]
        ]

        if stat.upper() == "perc".upper():
            x_max = np.max(tmp_in["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(tmp_in["-log(p-val)"])

        else:
            x_max = np.max(tmp_in["n"])

        # queue

        fig = self.bar_plot(
            data=tmp_in,
            n=n,
            side=side,
            color=color,
            width=width,
            bar_width=bar_width,
            stat=stat,
            sets="DISEASES",
            column=column,
            x_max=x_max,
            show_axis=True,
            title="DISEASES",
            ax=None,
        )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def set_ViMIC_plot(
        self,
        set_num=1,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n=5,
        side="right",
        color="aquamarine",
        width=10,
        bar_width=0.5,
        stat="p_val",
    ):

        sets = "ViMIC"
        column = "virus"

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        test_string = self.select_test(test, adj)

        tmp_in = pd.DataFrame(self.input_data[f"set_{set_num}"]["statistics"][sets])

        tmp_in = tmp_in[tmp_in[test_string] <= p_val]
        tmp_in[test_string] = (
            tmp_in[test_string]
            + np.min(tmp_in[test_string][tmp_in[test_string] != 0]) / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[test_string])
        tmp_in = tmp_in.reset_index(drop=True)

        if stat.upper() == "perc".upper():
            x_max = np.max(tmp_in["pct"])

        elif stat.upper() == "p_val".upper():
            x_max = np.max(tmp_in["-log(p-val)"])

        else:
            x_max = np.max(tmp_in["n"])

        # queue

        fig = self.bar_plot(
            data=tmp_in,
            n=n,
            side=side,
            color=color,
            width=width,
            bar_width=bar_width,
            stat=stat,
            sets="ViMIC",
            column=column,
            x_max=x_max,
            show_axis=True,
            title="ViMIC",
            ax=None,
        )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def set_blod_markers_plot(
        self, set_num=1, n=10, side="right", color="red", width=10, bar_width=0.5
    ):

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        tmp_in = pd.DataFrame(
            self.input_data[f"set_{set_num}"]["enrichment"]["HPA"]["HPA_blood_markers"]
        )

        x_max = max(
            np.log10(np.max(tmp_in["blood_concentration_IM[pg/L]"])),
            np.log10(np.max(tmp_in["blood_concentration_MS[pg/L]"])),
        )

        iter_set = ["blood_concentration_IM[pg/L]", "blood_concentration_MS[pg/L]"]

        hlist = []
        for it in iter_set:
            print(it)

            tmp_len = len(tmp_in[it][tmp_in[it] == tmp_in[it]])

            if float(tmp_len) > n:
                tn = n
                if tn < 6:
                    if tn < 2:
                        hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / (2.12 + ((6 - tn) / 10)))
                else:
                    hlist.append(tn / 2.1)

            else:
                tn = float(tmp_len)
                if tn < 6:
                    if tn < 2:
                        hlist.append(tn / (2.5 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / (2.12 + ((6 - tn) / 10)))

                else:
                    hlist.append(tn / 2.1)

        fig = plt.figure(figsize=(width, sum(hlist)))

        gs = GridSpec(len(hlist), 1, height_ratios=hlist)

        gs.update(hspace=len(hlist) / 30)

        for l, i in enumerate(iter_set):

            tmp = tmp_in[tmp_in[i] == tmp_in[i]]

            tmp[i] = np.log10(tmp[i])

            ax = fig.add_subplot(gs[l])

            show_axis = l + 1 == len(iter_set)

            self.bar_plot_blood(
                data=tmp,
                n=n,
                side=side,
                color=color,
                width=width,
                bar_width=bar_width,
                stat=i,
                sets="Blood markers",
                column="found_names",
                x_max=x_max,
                show_axis=show_axis,
                title=f"log({i})",
                ax=ax,
            )

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def set_GOPa_network_create(
        self,
        data_set: str = "GO-TERM",
        set_num=1,
        genes_inc: int = 10,
        gene_int: bool = True,
        genes_only: bool = True,
        min_con: int = 2,
        children_con: bool = False,
        include_childrend: bool = True,
        selected_parents: list = [],
        selected_genes: list = [],
    ):

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        input_data = self.input_data[f"set_{set_num}"]

        GOPa = pd.DataFrame(input_data["networks"][data_set])
        genes_list = list(set(GOPa["features"]))

        if len(selected_genes) > 0:
            to_select_genes = []
            for p in selected_genes:
                if p in list(GOPa["features"]):
                    to_select_genes.append(p)
                else:
                    print("\nCould not find {p} gene!")

            if len(to_select_genes) != 0:
                GOPa = GOPa[GOPa["features"].isin(to_select_genes)]
                genes_inc = max(genes_inc, len(to_select_genes))
            else:
                print("\nCould not use provided set of genes!")

        if data_set in ["GO-TERM", "KEGG", "REACTOME"]:

            GOPa_drop = GOPa[["parent", "children"]].drop_duplicates()

            GOPa_drop = Counter(list(GOPa_drop["parent"]))

            GOPa_drop = pd.DataFrame(GOPa_drop.items(), columns=["GOPa", "n"])

            GOPa_drop = list(GOPa_drop["GOPa"][GOPa_drop["n"] >= min_con])

            GOPa = GOPa[GOPa["parent"].isin(GOPa_drop)]

            del GOPa_drop

            if genes_inc > 0:

                genes_list = GOPa["features"]

                inter = None
                tmp_genes_list = []

                if gene_int:
                    inter = pd.DataFrame(input_data["statistics"]["interactions"])
                    inter = inter[inter["A"] != inter["B"]]
                    inter = inter[inter["A"].isin(genes_list)]
                    inter = inter[inter["B"].isin(genes_list)]
                    tmp_genes_list = list(set(list(inter["B"]) + list(inter["A"])))

                    if len(tmp_genes_list) > 0:
                        genes_list = tmp_genes_list

                genes_list = Counter(genes_list)

                genes_list = pd.DataFrame(genes_list.items(), columns=["features", "n"])

                genes_list = genes_list.sort_values("n", ascending=False)

                gene_GOPa_p = GOPa[["parent", "features"]][
                    GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
                ]
                gene_GOP_c = GOPa[["features", "children"]][
                    GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
                ]
                genes_list = list(genes_list["features"][:genes_inc])

                if genes_only:
                    GOPa = GOPa[GOPa["features"].isin(genes_list)]

                gene_GOPa_p.columns = ["parent", "children"]

                gene_GOPa_p["color"] = "gray"

                GOPa = pd.concat([GOPa[["parent", "children", "color"]], gene_GOPa_p])

                if len(tmp_genes_list) > 0:
                    if isinstance(inter, pd.DataFrame):
                        inter = inter[inter["A"].isin(genes_list)]
                        inter = inter[inter["B"].isin(genes_list)]
                        inter = inter[["A", "B"]]
                        inter.columns = ["parent", "children"]
                        inter["color"] = "red"

                        GOPa = pd.concat([GOPa, inter])

                if children_con:

                    gene_GOP_c.columns = ["parent", "children"]

                    gene_GOP_c["color"] = "gray"

                    GOPa = pd.concat(
                        [GOPa[["parent", "children", "color"]], gene_GOP_c]
                    )

                del gene_GOP_c, gene_GOPa_p

            gopa_list = list(GOPa["parent"]) + list(GOPa["children"])

            gopa_list = Counter(gopa_list)

            gopa_list = pd.DataFrame(gopa_list.items(), columns=["GOPa", "weight"])

            if len(selected_parents) > 0:
                to_select = []
                to_select_genes = []

                for p in selected_parents:
                    if p in list(GOPa["parent"]):
                        to_select.append(p)
                        t = list(GOPa["children"][GOPa["parent"] == p])
                        for i in t:
                            tg = [x for x in genes_list if x in list(GOPa["children"])]
                            if i in tg:
                                to_select_genes.append(i)

                    else:
                        print("\nCould not find {p} parent term!")

                if len(to_select) != 0:
                    GOPa = GOPa[
                        GOPa["parent"].isin(to_select + to_select_genes)
                        & GOPa["children"].isin(
                            list(GOPa["children"][GOPa["parent"].isin(to_select)])
                        )
                    ]
                    gopa_list = gopa_list[
                        gopa_list["GOPa"].isin(
                            list(GOPa["parent"]) + list(GOPa["children"])
                        )
                    ]

                else:
                    print("\nCould not use provided set of parent terms!")

            if include_childrend is False:
                GOPa = GOPa[GOPa["children"].isin(list(GOPa["parent"]) + genes_list)]
                gopa_list = gopa_list[
                    gopa_list["GOPa"].isin(list(GOPa["parent"]) + genes_list)
                ]

            G = nx.Graph()

            for _, row in gopa_list.iterrows():
                node = row["GOPa"]

                if node in genes_list:
                    color = "orange"
                    weight = np.log2(row["weight"] * 1000)

                elif node in list(GOPa["parent"]):
                    color = "cyan"
                    weight = np.log2(row["weight"] * 1000) * 2
                else:
                    color = "silver"
                    weight = np.log2(row["weight"] * 1000)

                G.add_node(node, size=weight, color=color)

            for _, row in GOPa.iterrows():
                source = row["parent"]
                target = row["children"]
                color = row["color"]
                G.add_edge(source, target, color=color)

            return G

        else:

            print("\nWrong data set selected!")
            print("\nAvaiable data sets are included in:")

            for i in ["GO-TERM", "KEGG", "DISEASES", "ViMIC", "REACTOME"]:
                print(f"\n{i}")

    def set_GI_network_create(
        self, set_num=1, data_set: str = "GO-TERM", min_con: int = 2
    ):

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        input_data = self.input_data[f"set_{set_num}"]

        inter = pd.DataFrame(input_data["statistics"]["interactions"])
        inter = inter[["A", "B", "connection_type"]]

        dict_meta = pd.DataFrame(
            {
                "interactions": [
                    ["gene -> gene"],
                    ["protein -> protein"],
                    ["gene -> protein"],
                    ["protein -> gene"],
                    ["gene -> gene", "protein -> protein"],
                    ["gene -> gene", "gene -> protein"],
                    ["gene -> gene", "protein -> gene"],
                    ["protein -> protein", "gene -> protein"],
                    ["protein -> protein", "protein -> gene"],
                    ["gene -> protein", "protein -> gene"],
                    ["gene -> gene", "protein -> protein", "gene -> protein"],
                    ["gene -> gene", "protein -> protein", "protein -> gene"],
                    ["gene -> gene", "gene -> protein", "protein -> gene"],
                    ["protein -> protein", "gene -> protein", "protein -> gene"],
                    [
                        "gene -> gene",
                        "protein -> protein",
                        "gene -> protein",
                        "protein -> gene",
                    ],
                ],
                "color": [
                    "#f67089",
                    "#f47832",
                    "#ca9213",
                    "#ad9d31",
                    "#8eb041",
                    "#4fb14f",
                    "#33b07a",
                    "#35ae99",
                    "#36acae",
                    "#38a9c5",
                    "#3aa3ec",
                    "#957cf4",
                    "#cd79f4",
                    "#f35fb5",
                    "#f669b7",
                ],
            }
        )

        genes_list = list(inter["A"]) + list(inter["B"])

        genes_list = Counter(genes_list)

        genes_list = pd.DataFrame(genes_list.items(), columns=["features", "n"])

        genes_list = genes_list.sort_values("n", ascending=False)

        genes_list = genes_list[genes_list["n"] >= min_con]

        inter = inter[inter["A"].isin(list(genes_list["features"]))]
        inter = inter[inter["B"].isin(list(genes_list["features"]))]

        inter = inter.groupby(["A", "B"]).agg({"connection_type": list}).reset_index()

        inter["color"] = "black"

        for inx in inter.index:
            for inx2 in dict_meta.index:
                if set(inter["connection_type"][inx]) == set(
                    dict_meta["interactions"][inx2]
                ):
                    inter["color"][inx] = dict_meta["color"][inx2]
                    break

        G = nx.Graph()

        for _, row in genes_list.iterrows():
            node = row["features"]
            color = "khaki"
            weight = np.log2(row["n"] * 500)
            G.add_node(node, size=weight, color=color)

        for _, row in inter.iterrows():
            source = row["A"]
            target = row["B"]
            color = row["color"]
            G.add_edge(source, target, color=color)

        return G

    def set_AUTO_ML_network(
        self,
        set_num=1,
        genes_inc: int = 10,
        gene_int: bool = True,
        genes_only: bool = True,
        min_con: int = 2,
        children_con: bool = False,
        include_childrend: bool = False,
        selected_parents: list = [],
        selected_genes: list = [],
    ):

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        input_data = self.input_data[f"set_{set_num}"]

        full_genes = []
        genes_sets = []
        GOPa = pd.DataFrame()
        for s in ["GO-TERM", "KEGG", "REACTOME"]:
            if s in input_data["networks"].keys():
                genes_sets.append(set(input_data["networks"][s]["features"]))
                full_genes += list(set(input_data["networks"][s]["features"]))
                tmp = pd.DataFrame(input_data["networks"][s])
                tmp["set"] = s
                tmp["color"] = "gray"
                GOPa = pd.concat([GOPa, tmp])

        common_elements = set.intersection(*genes_sets)

        del genes_sets

        inter = pd.DataFrame(input_data["statistics"]["interactions"])
        inter = inter[inter["A"].isin(full_genes)]
        inter = inter[inter["B"].isin(full_genes)]

        if len(common_elements) > 0:
            inter = inter[
                inter["A"].isin(common_elements) | inter["B"].isin(common_elements)
            ]

        selection_list = list(set(list(set(inter["B"])) + list(set(inter["A"]))))

        if len(selected_genes) > 0:
            to_select_genes = []
            for p in selected_genes:
                if p in list(GOPa["features"]):
                    to_select_genes.append(p)
                else:
                    print("\nCould not find {p} gene!")

            if len(to_select_genes) != 0:
                GOPa = GOPa[GOPa["features"].isin(to_select_genes)]
                genes_inc = max(genes_inc, len(to_select_genes))

            else:
                print("\nCould not use provided set of genes!")

        else:
            GOPa = GOPa[GOPa["features"].isin(selection_list)]

        GOPa_drop = GOPa[["parent", "children"]].drop_duplicates()

        GOPa_drop = Counter(list(GOPa_drop["parent"]))

        GOPa_drop = pd.DataFrame(GOPa_drop.items(), columns=["GOPa", "n"])

        GOPa_drop = list(GOPa_drop["GOPa"][GOPa_drop["n"] >= min_con])

        GOPa = GOPa[GOPa["parent"].isin(GOPa_drop)]

        del GOPa_drop

        if genes_inc > 0:

            genes_list = GOPa["features"]

            inter = None
            tmp_genes_list = []

            if gene_int:
                inter = pd.DataFrame(input_data["statistics"]["interactions"])
                inter = inter[inter["A"] != inter["B"]]
                inter = inter[inter["A"].isin(genes_list)]
                inter = inter[inter["B"].isin(genes_list)]
                tmp_genes_list = list(set(list(inter["B"]) + list(inter["A"])))

                if len(tmp_genes_list) > 0:
                    genes_list = tmp_genes_list

            genes_list = Counter(genes_list)

            genes_list = pd.DataFrame(genes_list.items(), columns=["features", "n"])

            genes_list = genes_list.sort_values("n", ascending=False)

            gene_GOPa_p = GOPa[["parent", "features", "set", "color"]][
                GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
            ]
            gene_GOP_c = GOPa[["features", "children", "set", "color"]][
                GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
            ]
            genes_list = list(genes_list["features"][:genes_inc])

            if genes_only:
                GOPa = GOPa[GOPa["features"].isin(genes_list)]

            gene_GOPa_p.columns = ["parent", "children", "set", "color"]

            GOPa = pd.concat(
                [GOPa[["parent", "children", "set", "color"]], gene_GOPa_p]
            )

            if len(tmp_genes_list) > 0:
                if isinstance(inter, pd.DataFrame):
                    inter = inter[inter["A"].isin(genes_list)]
                    inter = inter[inter["B"].isin(genes_list)]
                    inter = inter[["A", "B"]]
                    inter.columns = ["parent", "children"]
                    inter["set"] = "gene"
                    inter["color"] = "red"

                    GOPa = pd.concat([GOPa, inter])

            if children_con:

                gene_GOP_c.columns = ["parent", "children", "set", "color"]

                GOPa = pd.concat(
                    [GOPa[["parent", "children", "set", "color"]], gene_GOP_c]
                )

            del gene_GOP_c, gene_GOPa_p

        gopa_list = list(GOPa["parent"]) + list(GOPa["children"])

        gopa_list = Counter(gopa_list)

        gopa_list = pd.DataFrame(
            gopa_list.items(), columns=["GOPa", "weight"]
        ).reset_index(drop=True)

        gopa_list["set"] = None

        for inx in gopa_list.index:
            if gopa_list["GOPa"][inx] in list(GOPa["parent"]):
                gopa_list["set"][inx] = list(
                    GOPa["set"][GOPa["parent"] == gopa_list["GOPa"][inx]]
                )[0]
            elif gopa_list["GOPa"][inx] in list(GOPa["children"]):
                gopa_list["set"][inx] = list(
                    GOPa["set"][GOPa["children"] == gopa_list["GOPa"][inx]]
                )[0]

        if len(selected_parents) > 0:
            to_select = []
            to_select_genes = []

            for p in selected_parents:
                if p in list(GOPa["parent"]):
                    to_select.append(p)
                    t = list(GOPa["children"][GOPa["parent"] == p])
                    for i in t:
                        tg = [x for x in genes_list if x in list(GOPa["children"])]
                        if i in tg:
                            to_select_genes.append(i)

                else:
                    print("\nCould not find {p} parent term!")

            if len(to_select) != 0:
                GOPa = GOPa[
                    GOPa["parent"].isin(to_select + to_select_genes)
                    & GOPa["children"].isin(
                        list(GOPa["children"][GOPa["parent"].isin(to_select)])
                    )
                ]
                gopa_list = gopa_list[
                    gopa_list["GOPa"].isin(
                        list(GOPa["parent"]) + list(GOPa["children"])
                    )
                ]

            else:
                print("\nCould not use provided set of parent terms!")

        if include_childrend is False:
            GOPa = GOPa[GOPa["children"].isin(list(GOPa["parent"]) + genes_list)]
            gopa_list = gopa_list[
                gopa_list["GOPa"].isin(list(GOPa["parent"]) + genes_list)
            ]

        G = nx.Graph()

        for _, row in gopa_list.iterrows():
            node = row["GOPa"]

            color = "black"

            if node in genes_list:
                color = "orange"
                weight = np.log2(row["weight"] * 1000)

            elif node in list(GOPa["parent"]):
                color = "cyan"
                weight = np.log2(row["weight"] * 1000) * 2

            else:
                if row["set"] == "GO-TERM":
                    color = "bisque"
                    weight = np.log2(row["weight"] * 1000)

                elif row["set"] == "KEGG":
                    color = "mistyrose"
                    weight = np.log2(row["weight"] * 1000)

                elif row["set"] == "REACTOME":
                    color = "darkkhaki"
                    weight = np.log2(row["weight"] * 1000)

            G.add_node(node, size=weight, color=color)

        for _, row in GOPa.iterrows():
            source = row["parent"]
            target = row["children"]
            color = row["color"]
            G.add_edge(source, target, color=color)

        return G

    def set_gene_scatter(
        self,
        set_num=1,
        colors="viridis",
        species="human",
        hclust="complete",
        img_width=None,
        img_high=None,
        label_size=None,
        x_lab="Genes",
        legend_lab="log(TPM + 1)",
        selected_list: list = [],
    ):
        """
        This function creates a graph in the format of a scatter plot for expression data prepared in data frame format.

        Args:
            data (data frame) - data frame of genes/protein expression where on row are the gene/protein names and on column grouping variable (tissue / cell / ect. names)
            color (str) - palette color available for matplotlib in python eg. viridis
            species (str) - species for upper() or lower() letter for gene/protein name depending on
            hclust (str) - type of data clustering of input expression data eg. complete or None if  no clustering
            img_width (float) - width of the image or None for auto-adjusting
            img_high (float) - high of the image or None for auto-adjusting
            label_size (float) - labels size of the image or None for auto-adjusting
            x_lab (str) - tex for x axis label
            legend_lab (str) - description for legend label


        Returns:
            graph: Scatter plot of expression data
        """

        if set_num not in [1, 2]:
            raise ValueError("Wrong set_num. Avaiable set number in 1 or 2!")

        input_data = self.input_data[f"set_{set_num}"]["enrichment"]["RNA-SEQ"]

        return_dict = {}

        for i in input_data.keys():
            data = pd.DataFrame(input_data[i])
            data.index = data["tissue"]
            data.pop("tissue")

            if len(selected_list) > 0:
                selected_list = [y.upper() for y in selected_list]
                to_select = [x for x in data.columns if x.upper() in selected_list]
                data = data.loc[:, to_select]

            scatter_df = data

            if img_width is None:
                img_width = len(scatter_df.columns) * 1.2

            if img_high is None:
                img_high = len(scatter_df.index) * 0.9

            if label_size is None:
                label_size = np.log(len(scatter_df.index) * len(scatter_df.index)) * 2.5

                if label_size < 7:
                    label_size = 7

            cm = 1 / 2.54

            if len(scatter_df) > 1:

                Z = linkage(scatter_df, method=hclust)

                order_of_features = dendrogram(Z, no_plot=True)["leaves"]

                indexes_sort = list(scatter_df.index)
                sorted_list_rows = []
                for n in order_of_features:
                    sorted_list_rows.append(indexes_sort[n])

                scatter_df = scatter_df.transpose()

                Z = linkage(scatter_df, method=hclust)

                order_of_features = dendrogram(Z, no_plot=True)["leaves"]

                indexes_sort = list(scatter_df.index)
                sorted_list_columns = []
                for n in order_of_features:
                    sorted_list_columns.append(indexes_sort[n])

                scatter_df = scatter_df.transpose()

                scatter_df = scatter_df.loc[sorted_list_rows, sorted_list_columns]

            scatter_df = np.log(scatter_df + 1)
            scatter_df[scatter_df <= np.mean(scatter_df.quantile(0.10))] = (
                np.mean(np.mean(scatter_df, axis=1)) / 10
            )

            if species.lower() == "human":
                scatter_df.index = [x.upper() for x in scatter_df.index]
            else:
                scatter_df.index = [x.title() for x in scatter_df.index]

            scatter_df.insert(0, "  ", 0)

            scatter_df[" "] = 0

            fig, ax = plt.subplots(figsize=(img_width * cm, img_high * cm))

            plt.scatter(
                x=[*range(0, len(scatter_df.columns), 1)],
                y=[" "] * len(scatter_df.columns),
                s=0,
                cmap=colors,
                edgecolors=None,
            )

            for index, row in enumerate(scatter_df.index):
                x = [*range(0, len(np.array(scatter_df.loc[row,])), 1)]
                y = [row] * len(x)
                s = np.array(scatter_df.loc[row,])
                plt.scatter(
                    x,
                    y,
                    s=np.log(s + 1) * 70,
                    c=s,
                    cmap=colors,
                    edgecolors="black",
                    vmin=np.array(scatter_df).min(),
                    vmax=np.array(scatter_df).max(),
                    linewidth=0.00001,
                )
                sm = plt.cm.ScalarMappable(cmap=colors)
                sm.set_clim(
                    vmin=np.array(scatter_df).min(), vmax=np.array(scatter_df).max()
                )
                plt.xticks(x, scatter_df.columns)
                plt.ylabel(str(x_lab), fontsize=label_size)

            plt.scatter(
                x=[*range(0, len(scatter_df.columns), 1)],
                y=[""] * len(scatter_df.columns),
                s=0,
                cmap=colors,
                edgecolors=None,
            )

            plt.xticks(rotation=80)
            plt.tight_layout()
            plt.margins(0.005)
            plt.xticks(fontsize=label_size)
            plt.yticks(fontsize=label_size)

            len_bar = ax.get_position().height / 5
            if len(scatter_df) < 15:
                len_bar = 0.65

                cbar = fig.colorbar(sm, ax=ax)
                cbar.ax.set_ylabel(str(legend_lab), fontsize=label_size * 0.9)
                cbar.ax.yaxis.set_ticks_position("right")
                cbar.ax.set_position(
                    [
                        ax.get_position().x1 + 0.05,
                        (ax.get_position().y0 + ax.get_position().y1) / 1.9,
                        ax.get_position().width / 0.05,
                        len_bar,
                    ]
                )
                cbar.ax.yaxis.set_label_position("right")
                cbar.ax.yaxis.set_tick_params(labelsize=label_size * 0.8)
                cbar.outline.set_edgecolor("none")
            else:
                cbar = fig.colorbar(sm, ax=ax)
                cbar.ax.set_ylabel(str(legend_lab), fontsize=label_size * 0.9)
                cbar.ax.yaxis.set_ticks_position("right")
                cbar.ax.set_position(
                    [
                        ax.get_position().x1 + 0.05,
                        (ax.get_position().y0 + ax.get_position().y1) / 1.45,
                        ax.get_position().width / 0.05,
                        len_bar,
                    ]
                )
                cbar.ax.yaxis.set_label_position("right")
                cbar.ax.yaxis.set_tick_params(labelsize=label_size * 0.8)
                cbar.outline.set_edgecolor("none")

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["bottom"].set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.xaxis.set_tick_params(length=0, labelbottom=True)
            ax.yaxis.set_tick_params(length=0, labelbottom=True)
            ax.grid(False)

            if self.show_plot:
                plt.show()
            elif self.show_plot is False:
                plt.close(fig)

            return_dict[i] = fig

        return return_dict

    ###################################################################################
    # Differenational set analysis visualization

    def bar_plot_diff(
        self,
        data,
        side="right",
        color="blue",
        width=10,
        bar_width=0.5,
        stat="p_val",
        column="name",
        x_max=None,
        show_axis=True,
        title=None,
        ax=None,
    ):

        tmp = pd.DataFrame(data)

        if stat.upper() == "perc".upper():
            x_label = "Percent of genes [%]"
            values = tmp["pct"]
        elif stat.upper() == "p_val".upper():
            x_label = "-log(p-val)"
            values = tmp["-log(p-val)"]
        else:
            x_label = "Number of genes"
            values = tmp["n"]

        if ax is None:
            fig_1, ax = plt.subplots(figsize=(width, float(len(tmp[column]) / 2.5)))

        if side == "left":
            ax.barh(tmp[column], values, color=color, height=bar_width)
            ax.set_xlim(0, x_max)
            ax.invert_xaxis()
            ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

        else:
            ax.barh(tmp[column], values, color=color, height=bar_width)
            ax.set_xlim(0, x_max)
            ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

        if show_axis:
            ax.set_xlabel(x_label)
        else:
            ax.spines["bottom"].set_visible(False)
            ax.tick_params(
                axis="x", which="both", bottom=False, top=False, labelbottom=False
            )

        ax.set_ylabel("")
        ax.invert_yaxis()

        if title:
            ax.set_title(title)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

        if side == "right":
            ax.set_title("")
            ax.yaxis.tick_right()

        if ax is None:

            if self.show_plot:
                plt.show()
            elif self.show_plot is False:
                plt.close(fig_1)

        try:
            return fig_1
        except:
            return ax

    def create_inter_df(
        self,
        data_1: pd.DataFrame,
        data_2: pd.DataFrame(),
        group_by: str,
        values: str,
        set_col=None,
    ):

        if isinstance(set_col, str):
            data_1 = data_1[[group_by, values, set_col]]
            data_2 = data_2[[group_by, values, set_col]]

            return_data = pd.DataFrame()

            iter_sters = set(list(data_1[set_col]) + list(data_2[set_col]))

            for s in iter_sters:

                tmp1 = data_1[data_1[set_col] == s]
                tmp2 = data_2[data_2[set_col] == s]

                tmp_1_1 = tmp2[~tmp2[group_by].isin(tmp1[group_by])]
                tmp_1_1[values] = 0
                tmp_2_1 = tmp1[~tmp1[group_by].isin(tmp2[group_by])]
                tmp_2_1[values] = 0

                tmp1 = pd.concat([tmp1, tmp_1_1])
                tmp2 = pd.concat([tmp2, tmp_2_1])

                tmp1 = tmp1.drop(columns=[set_col])
                tmp2 = tmp2.drop(columns=[set_col])

                tmp_full = tmp1.merge(
                    tmp2, on=group_by, how="left", suffixes=("_1", "_2")
                )

                tmp_full[set_col] = s

                return_data = pd.concat([return_data, tmp_full])

        else:

            data_1 = data_1[[group_by, values]]
            data_2 = data_2[[group_by, values]]

            return_data = pd.DataFrame()

            tmp1 = data_1
            tmp2 = data_2

            tmp_1_1 = tmp2[~tmp2[group_by].isin(tmp1[group_by])]
            tmp_1_1[values] = 0
            tmp_2_1 = tmp1[~tmp1[group_by].isin(tmp2[group_by])]
            tmp_2_1[values] = 0

            tmp1 = pd.concat([tmp1, tmp_1_1])
            tmp2 = pd.concat([tmp2, tmp_2_1])

            return_data = tmp1.merge(
                tmp2, on=group_by, how="left", suffixes=("_1", "_2")
            )

        return return_data

    def bivector_column(
        self,
        plot_bin_data: pd.DataFrame,
        bin_value: str,
        name_col: str,
        set_col,
        min_n,
        n_max,
        width,
        bar_width,
        selected_set=[],
        inter_focus=False,
        s1_color="blue",
        s2_color="red",
        sep_factor=15,
    ):

        if bin_value.upper() == "perc".upper():
            val = "pct"
        elif bin_value.upper() == "p_val".upper():
            val = "-log(p-val)"
        else:
            val = "n"

        # select itteration

        iter_set = list(set(plot_bin_data[set_col]))

        if len(selected_set) > 0:
            tmp_iter = []
            for i in selected_set:
                if i in iter_set:
                    tmp_iter.append(i)
                else:
                    print(f"\nSet name: {i} was not found")

            iter_set = tmp_iter

            if len(iter_set) == 0:
                raise ValueError("Nothing to return")

        # select display data

        display_data = pd.DataFrame()

        for l, i in enumerate(iter_set):

            tmp = plot_bin_data[plot_bin_data[set_col] == i]

            q1_tmp = tmp[(tmp[val + "_1"] != 0) & (tmp[val + "_2"] == 0)]
            q3_tmp = tmp[(tmp[val + "_2"] != 0) & (tmp[val + "_1"] == 0)]
            q2_tmp = tmp[(tmp[val + "_2"] != 0) & (tmp[val + "_1"] != 0)]

            if len(tmp.index) >= min_n:

                if len(tmp.index) > n_max:

                    if inter_focus:

                        if len(q2_tmp.index) >= n_max:

                            q2_tmp = q2_tmp.sort_values(
                                by=[val + "_1", val + "_2"], ascending=[False, False]
                            ).reset_index(drop=True)

                            tmp = q2_tmp.iloc[0:n_max, :]

                        else:

                            q2_n = len(q2_tmp.index)

                            rest_n = n_max - q2_n

                            if rest_n % 2 != 0:
                                rest_n += 1

                            q1_tmp = q1_tmp.sort_values(
                                by=[val + "_1"], ascending=[False]
                            ).reset_index(drop=True)

                            q3_tmp = q3_tmp.sort_values(
                                by=[val + "_2"], ascending=[False]
                            ).reset_index(drop=True)

                            tmp = pd.concat(
                                [
                                    q2_tmp,
                                    q1_tmp.iloc[0 : rest_n / 2, :],
                                    q3_tmp.iloc[0 : rest_n / 2, :],
                                ]
                            )

                    else:

                        q1_n = len(q1_tmp.index)
                        q2_n = len(q2_tmp.index)
                        q3_n = len(q3_tmp.index)

                        q1_n = int(n_max * (q1_n / len(tmp.index)))
                        q2_n = int(n_max * (q2_n / len(tmp.index)))
                        q3_n = int(n_max * (q3_n / len(tmp.index)))

                        q2_tmp = q2_tmp.sort_values(
                            by=[val + "_1", val + "_2"], ascending=[False, False]
                        ).reset_index(drop=True)

                        q1_tmp = q1_tmp.sort_values(
                            by=[val + "_1"], ascending=[False]
                        ).reset_index(drop=True)

                        q3_tmp = q3_tmp.sort_values(
                            by=[val + "_2"], ascending=[False]
                        ).reset_index(drop=True)

                        tmp = pd.concat(
                            [
                                q2_tmp.iloc[0:q2_n, :],
                                q1_tmp.iloc[0:q1_n, :],
                                q3_tmp.iloc[0:q3_n, :],
                            ]
                        )

            tmp["sort_category"] = 1
            tmp.loc[
                (tmp[val + "_1"] != 0) & (tmp[val + "_2"] != 0), "sort_category"
            ] = 2
            tmp.loc[tmp[val + "_1"] == 0, "sort_category"] = 3

            tmp = (
                tmp.sort_values(
                    by=["sort_category", val + "_1", val + "_2"],
                    ascending=[True, False, True],
                )
                .drop(columns=["sort_category"])
                .reset_index(drop=True)
            )

            display_data = pd.concat([display_data, tmp])

        # set queue

        tmp_q = display_data.copy()
        tmp_q["sort"] = tmp_q[val + "_1"] + tmp_q[val + "_2"]

        tmp_q = tmp_q[[set_col, "sort"]]
        tmp_q = tmp_q.groupby(set_col, as_index=False).sum()
        tmp_q = tmp_q.sort_values(by="sort", ascending=False).reset_index(drop=True)

        iter_set = list(tmp_q[set_col])

        # set plot distance

        hlist = []

        valid_iter_set = []

        x_max = 0

        for l, i in enumerate(iter_set):

            tmp_in = display_data[display_data[set_col] == i]

            #

            if len(set(tmp_in[name_col])) >= min_n:

                valid_iter_set.append(i)
                x_max = np.max(
                    [x_max] + list(tmp_in[val + "_1"]) + list(tmp_in[val + "_2"])
                )

                if float(len(set(tmp_in[name_col]))) > n_max:

                    tn = n_max
                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (3.25 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))
                    else:
                        hlist.append(tn / 2.1)

                else:

                    tn = float(len(set(tmp_in[name_col])))

                    if tn < 6:
                        if tn < 2:
                            hlist.append(tn / (3.25 + ((6 - tn) / 10)))
                        else:
                            hlist.append(tn / (2.12 + ((6 - tn) / 10)))

                    else:
                        hlist.append(tn / 2.1)

        iter_set_final = valid_iter_set

        fig = plt.figure(figsize=(width, sum(hlist)))

        gs = GridSpec(len(hlist), 2, height_ratios=hlist)

        plt.subplots_adjust(wspace=0.05)

        gs.update(hspace=len(hlist) / sep_factor)

        for l, i in enumerate(iter_set_final):

            ax1 = fig.add_subplot(gs[l, 0])
            ax2 = fig.add_subplot(gs[l, 1])
            ax1.tick_params(
                axis="y",
                which="both",
                left=False,
                right=False,
                labelleft=False,
                labelright=False,
                colors="white",
            )

            tmp = display_data[display_data[set_col] == i]

            tmp1 = tmp[[name_col, val + "_1"]]
            tmp1.rename(columns={val + "_1": val}, inplace=True)
            tmp2 = tmp[[name_col, val + "_2"]]
            tmp2.rename(columns={val + "_2": val}, inplace=True)

            # plots creating

            show_axis = l + 1 == len(iter_set_final)

            self.bar_plot_diff(
                data=tmp1,
                side="left",
                color=s1_color,
                width=width,
                bar_width=bar_width,
                stat=bin_value,
                column=name_col,
                x_max=x_max,
                show_axis=show_axis,
                title=i,
                ax=ax1,
            )

            self.bar_plot_diff(
                data=tmp2,
                side="right",
                color=s2_color,
                width=width,
                bar_width=bar_width,
                stat=bin_value,
                column=name_col,
                x_max=x_max,
                show_axis=show_axis,
                title=i,
                ax=ax2,
            )

        plt.tight_layout()

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig

    def diff_GO_plot(
        self,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n: int = 25,
        min_terms: int = 5,
        selected_parent: list = [],
        width=10,
        bar_width=0.5,
        stat="p_val",
        sep_factor=15,
    ):
        """
        This method generates a bar plot for Gene Ontology (GO) Differential Set Analysis (DES) of enrichment and statistical analysis.
        Results for set1 are displayed on the left side of the graph, while results for set2 are shown on the right side.

            Args:
                p_val (float) - significance threshold for p-values. Default is 0.05
                test (str) - statistical test to use ('FISH' - Fisher's Exact Test or 'BIN' - binomial test). Default is 'FISH'
                adj (str) - method for p-value adjustment ('BH' - Benjamini-Hochberg, 'BF' - Benjamini-Hochberg). Default is 'BH'
                n (int) - maximum number of terms to display per category. Default is 25
                min_terms (int) - minimum number of child terms required for a parent term to be included. Default is 5
                selected_parent (list) - list of specific parent terms to include in the plot. If empty, all parent terms are included. Default is []
                side (str) - side on which the bars are displayed ('left' or 'right'). Default is 'right'
                color (str) - color of the bars in the plot. Default is 'blue'
                width (int) - width of the plot in inches. Default is 10
                bar_width (float / int) - width of individual bars. Default is 0.5
                stat (str) - statistic to use for the x-axis ('p_val', 'n', or 'perc'). Default is 'p_val'

            Returns:
                fig (matplotlib.figure.Figure) - matplotlib Figure object containing the bar plots
        """

        sets = "GO-TERM"

        test_string = self.select_test(test, adj)

        # loading meta

        metadata = pd.DataFrame(self.input_data["regulations"]["GO-TERM"])

        # set1

        tmp_in = pd.DataFrame(self.input_data["set_1"]["statistics"][sets])
        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"parent_{test_string}"] <= p_val]
        tmp_in = tmp_in[tmp_in[f"child_{test_string}"] <= p_val]
        tmp_in[f"child_{test_string}"] = (
            tmp_in[f"child_{test_string}"]
            + np.min(
                tmp_in[f"child_{test_string}"][tmp_in[f"child_{test_string}"] != 0]
            )
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"child_{test_string}"])
        tmp_in["n"] = tmp_in["child_n"]
        tmp_in["pct"] = tmp_in["child_pct"]

        tmp_in_1 = tmp_in.reset_index(drop=True)

        parent = list(
            metadata["term"][
                (metadata["type"] == "parent")
                & (
                    (metadata["regulation"] == "s1")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        child = list(
            metadata["term"][
                (metadata["type"] == "children")
                & (
                    (metadata["regulation"] == "s1")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        tmp_in_1 = tmp_in_1[
            tmp_in_1["parent_name"].isin(parent) | tmp_in_1["child_name"].isin(child)
        ]

        # set2

        tmp_in = pd.DataFrame(self.input_data["set_2"]["statistics"][sets])
        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"parent_{test_string}"] <= p_val]
        tmp_in = tmp_in[tmp_in[f"child_{test_string}"] <= p_val]
        tmp_in[f"child_{test_string}"] = (
            tmp_in[f"child_{test_string}"]
            + np.min(
                tmp_in[f"child_{test_string}"][tmp_in[f"child_{test_string}"] != 0]
            )
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"child_{test_string}"])
        tmp_in["n"] = tmp_in["child_n"]
        tmp_in["pct"] = tmp_in["child_pct"]

        tmp_in_2 = tmp_in.reset_index(drop=True)

        parent = list(
            metadata["term"][
                (metadata["type"] == "parent")
                & (
                    (metadata["regulation"] == "s2")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        child = list(
            metadata["term"][
                (metadata["type"] == "children")
                & (
                    (metadata["regulation"] == "s2")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        tmp_in_2 = tmp_in_2[
            tmp_in_2["parent_name"].isin(parent) | tmp_in_2["child_name"].isin(child)
        ]

        ##############################################################################

        if stat.upper() == "perc".upper():
            val = "pct"
        elif stat.upper() == "p_val".upper():
            val = "-log(p-val)"
        else:
            val = "n"

        plot_bin_data = self.create_inter_df(
            data_1=tmp_in_1,
            data_2=tmp_in_2,
            group_by="child_name",
            values=val,
            set_col="parent_name",
        )

        plot = self.bivector_column(
            plot_bin_data=plot_bin_data,
            bin_value=stat,
            name_col="child_name",
            set_col="parent_name",
            min_n=min_terms,
            n_max=n,
            width=width,
            bar_width=bar_width,
            selected_set=selected_parent,
            inter_focus=False,
            s1_color="lightblue",
            s2_color="blue",
            sep_factor=sep_factor,
        )

        ##############################################################################

        return plot

    def diff_KEGG_plot(
        self,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n: int = 25,
        min_terms: int = 5,
        selected_parent: list = [],
        width=10,
        bar_width=0.5,
        stat="p_val",
        sep_factor=15,
    ):
        """
        This method generates a bar plot for KEGG Differential Set Analysis (DES) of enrichment and statistical analysis.
        Results for set1 are displayed on the left side of the graph, while results for set2 are shown on the right side.

        Args:
            p_val (float) - significance threshold for p-values. Default is 0.05
            test (str) - statistical test to use ('FISH' - Fisher's Exact Test or 'BIN' - binomial test). Default is 'FISH'
            adj (str) - method for p-value adjustment ('BH' - Benjamini-Hochberg, 'BF' - Benjamini-Hochberg). Default is 'BH'
            n (int) - maximum number of terms to display per category. Default is 25
            min_terms (int) - minimum number of child terms required for a parent term to be included. Default is 5
            selected_parent (list) - list of specific parent terms to include in the plot. If empty, all parent terms are included. Default is []
            side (str) - side on which the bars are displayed ('left' or 'right'). Default is 'right'
            color (str) - color of the bars in the plot. Default is 'orange'
            width (int) - width of the plot in inches. Default is 10
            bar_width (float / int) - width of individual bars. Default is 0.5
            stat (str) - statistic to use for the x-axis ('p_val', 'n', or 'perc'). Default is 'p_val'

        Returns:
            fig (matplotlib.figure.Figure) - matplotlib Figure object containing the bar plots
        """

        sets = "KEGG"

        test_string = self.select_test(test, adj)

        # loading meta

        metadata = pd.DataFrame(self.input_data["regulations"]["KEGG"])

        # set1

        tmp_in = pd.DataFrame(self.input_data["set_1"]["statistics"][sets])
        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"2nd_{test_string}"] <= p_val]
        tmp_in = tmp_in[tmp_in[f"3rd_{test_string}"] <= p_val]
        tmp_in[f"3rd_{test_string}"] = (
            tmp_in[f"3rd_{test_string}"]
            + np.min(tmp_in[f"3rd_{test_string}"][tmp_in[f"3rd_{test_string}"] != 0])
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"3rd_{test_string}"])
        tmp_in["n"] = tmp_in["3rd_n"]
        tmp_in["pct"] = tmp_in["3rd_pct"]

        tmp_in_1 = tmp_in.reset_index(drop=True)

        parent = list(
            metadata["term"][
                (metadata["type"] == "parent")
                & (
                    (metadata["regulation"] == "s1")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        child = list(
            metadata["term"][
                (metadata["type"] == "children")
                & (
                    (metadata["regulation"] == "s1")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        tmp_in_1 = tmp_in_1[tmp_in_1["2nd"].isin(parent) | tmp_in_1["3rd"].isin(child)]

        # set2

        tmp_in = pd.DataFrame(self.input_data["set_2"]["statistics"][sets])
        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"2nd_{test_string}"] <= p_val]
        tmp_in = tmp_in[tmp_in[f"3rd_{test_string}"] <= p_val]
        tmp_in[f"3rd_{test_string}"] = (
            tmp_in[f"3rd_{test_string}"]
            + np.min(tmp_in[f"3rd_{test_string}"][tmp_in[f"3rd_{test_string}"] != 0])
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"3rd_{test_string}"])
        tmp_in["n"] = tmp_in["3rd_n"]
        tmp_in["pct"] = tmp_in["3rd_pct"]

        tmp_in_2 = tmp_in.reset_index(drop=True)

        parent = list(
            metadata["term"][
                (metadata["type"] == "parent")
                & (
                    (metadata["regulation"] == "s2")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        child = list(
            metadata["term"][
                (metadata["type"] == "children")
                & (
                    (metadata["regulation"] == "s2")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        tmp_in_2 = tmp_in_2[tmp_in_2["2nd"].isin(parent) | tmp_in_2["3rd"].isin(child)]

        ##############################################################################

        if stat.upper() == "perc".upper():
            val = "pct"
        elif stat.upper() == "p_val".upper():
            val = "-log(p-val)"
        else:
            val = "n"

        plot_bin_data = self.create_inter_df(
            data_1=tmp_in_1, data_2=tmp_in_2, group_by="3rd", values=val, set_col="2nd"
        )

        plot = self.bivector_column(
            plot_bin_data=plot_bin_data,
            bin_value=stat,
            name_col="3rd",
            set_col="2nd",
            min_n=min_terms,
            n_max=n,
            width=width,
            bar_width=bar_width,
            selected_set=selected_parent,
            inter_focus=False,
            s1_color="moccasin",
            s2_color="orange",
            sep_factor=sep_factor,
        )

        ##############################################################################

        return plot

    def diff_REACTOME_plot(
        self,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n: int = 25,
        min_terms: int = 5,
        selected_parent: list = [],
        width=10,
        bar_width=0.5,
        stat="p_val",
        sep_factor=15,
    ):
        """
        This method generates a bar plot for Reactome Differential Set Analysis (DES) of enrichment and statistical analysis.
        Results for set1 are displayed on the left side of the graph, while results for set2 are shown on the right side.

        Args:
            p_val (float) - significance threshold for p-values. Default is 0.05
            test (str) - statistical test to use ('FISH' - Fisher's Exact Test or 'BIN' - binomial test). Default is 'FISH'
            adj (str) - method for p-value adjustment ('BH' - Benjamini-Hochberg, 'BF' - Benjamini-Hochberg). Default is 'BH'
            n (int) - maximum number of terms to display per category. Default is 25
            min_terms (int) - minimum number of child terms required for a parent term to be included. Default is 5
            selected_parent (list) - list of specific parent terms to include in the plot. If empty, all parent terms are included. Default is []
            side (str) - side on which the bars are displayed ('left' or 'right'). Default is 'right'
            color (str) - color of the bars in the plot. Default is 'silver'
            width (int) - width of the plot in inches. Default is 10
            bar_width (float / int) - width of individual bars. Default is 0.5
            stat (str) - statistic to use for the x-axis ('p_val', 'n', or 'perc'). Default is 'p_val'

        Returns:
            fig (matplotlib.figure.Figure) - matplotlib Figure object containing the bar plots
        """

        sets = "REACTOME"

        test_string = self.select_test(test, adj)

        # loading meta

        metadata = pd.DataFrame(self.input_data["regulations"]["REACTOME"])

        # set1

        tmp_in = pd.DataFrame(self.input_data["set_1"]["statistics"][sets])
        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"top_level_pathway_{test_string}"] <= p_val]
        tmp_in = tmp_in[tmp_in[f"pathway_{test_string}"] <= p_val]
        tmp_in[f"pathway_{test_string}"] = (
            tmp_in[f"pathway_{test_string}"]
            + np.min(
                tmp_in[f"pathway_{test_string}"][tmp_in[f"pathway_{test_string}"] != 0]
            )
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"pathway_{test_string}"])
        tmp_in["n"] = tmp_in["pathway_n"]
        tmp_in["pct"] = tmp_in["pathway_pct"]

        tmp_in_1 = tmp_in.reset_index(drop=True)

        parent = list(
            metadata["term"][
                (metadata["type"] == "parent")
                & (
                    (metadata["regulation"] == "s1")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        child = list(
            metadata["term"][
                (metadata["type"] == "children")
                & (
                    (metadata["regulation"] == "s1")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        tmp_in_1 = tmp_in_1[
            tmp_in_1["top_level_pathway"].isin(parent) | tmp_in_1["pathway"].isin(child)
        ]

        # set2

        tmp_in = pd.DataFrame(self.input_data["set_2"]["statistics"][sets])
        if self.parent_stats:
            tmp_in = tmp_in[tmp_in[f"top_level_pathway_{test_string}"] <= p_val]
        tmp_in = tmp_in[tmp_in[f"pathway_{test_string}"] <= p_val]
        tmp_in[f"pathway_{test_string}"] = (
            tmp_in[f"pathway_{test_string}"]
            + np.min(
                tmp_in[f"pathway_{test_string}"][tmp_in[f"pathway_{test_string}"] != 0]
            )
            / 2
        )
        tmp_in["-log(p-val)"] = -np.log(tmp_in[f"pathway_{test_string}"])
        tmp_in["n"] = tmp_in["pathway_n"]
        tmp_in["pct"] = tmp_in["pathway_pct"]

        tmp_in_2 = tmp_in.reset_index(drop=True)

        parent = list(
            metadata["term"][
                (metadata["type"] == "parent")
                & (
                    (metadata["regulation"] == "s2")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        child = list(
            metadata["term"][
                (metadata["type"] == "children")
                & (
                    (metadata["regulation"] == "s2")
                    | (metadata["regulation"] == "equal")
                )
            ]
        )

        tmp_in_2 = tmp_in_2[
            tmp_in_2["top_level_pathway"].isin(parent) | tmp_in_2["pathway"].isin(child)
        ]

        ##############################################################################

        if stat.upper() == "perc".upper():
            val = "pct"
        elif stat.upper() == "p_val".upper():
            val = "-log(p-val)"
        else:
            val = "n"

        plot_bin_data = self.create_inter_df(
            data_1=tmp_in_1,
            data_2=tmp_in_2,
            group_by="pathway",
            values=val,
            set_col="top_level_pathway",
        )

        plot = self.bivector_column(
            plot_bin_data=plot_bin_data,
            bin_value=stat,
            name_col="pathway",
            set_col="top_level_pathway",
            min_n=min_terms,
            n_max=n,
            width=width,
            bar_width=bar_width,
            selected_set=selected_parent,
            inter_focus=False,
            s1_color="lightgray",
            s2_color="darkgray",
            sep_factor=sep_factor,
        )

        ##############################################################################

        return plot

    def diff_SPECIFICITY_plot(
        self,
        p_val=0.05,
        test="FISH",
        adj="BH",
        n=5,
        min_terms: int = 1,
        selected_set: list = [],
        width=10,
        bar_width=0.5,
        stat="p_val",
        sep_factor=15,
    ):
        """
        This method generates a bar plot for tissue specificity [Human Protein Atlas (HPA)] Differential Set Analysis (DES) of enrichment and statistical analysis.
        Results for set1 are displayed on the left side of the graph, while results for set2 are shown on the right side.

        Args:
            p_val (float) - significance threshold for p-values. Default is 0.05
            test (str) - statistical test to use ('FISH' - Fisher's Exact Test or 'BIN' - binomial test). Default is 'FISH'
            adj (str) - method for p-value adjustment ('BH' - Benjamini-Hochberg, 'BF' - Benjamini-Hochberg). Default is 'BH'
            n (int) - maximum number of terms to display per category. Default is 5
            side (str) - side on which the bars are displayed ('left' or 'right'). Default is 'right'
            color (str) - color of the bars in the plot. Default is 'bisque'
            width (int) - width of the plot in inches. Default is 10
            bar_width (float / int) - width of individual bars. Default is 0.5
            stat (str) - statistic to use for the x-axis ('p_val', 'n', or 'perc'). Default is 'p_val'

        Returns:
            fig (matplotlib.figure.Figure) - matplotlib Figure object containing the bar plots
        """

        sets = "specificity"

        test_string = self.select_test(test, adj)

        full_metadata = pd.DataFrame(self.input_data["regulations"]["specificity"])

        full_df_1 = pd.DataFrame()
        full_df_2 = pd.DataFrame()

        for si in self.input_data["set_1"]["statistics"][sets].keys():

            metadata = pd.DataFrame(full_metadata[full_metadata["set"] == si])

            # set1

            tmp_in = pd.DataFrame(self.input_data["set_1"]["statistics"][sets][si])
            tmp_in = tmp_in[tmp_in[test_string] <= p_val]
            tmp_in[test_string] = (
                tmp_in[test_string]
                + np.min(tmp_in[test_string][tmp_in[test_string] != 0]) / 2
            )
            tmp_in["-log(p-val)"] = -np.log(tmp_in[test_string])

            tmp_in_1 = tmp_in.reset_index(drop=True)

            terms = list(
                metadata["term"][
                    (metadata["regulation"] == "s1")
                    | (metadata["regulation"] == "equal")
                ]
            )

            tmp_in_1 = tmp_in_1[tmp_in_1["specificity"].isin(terms)]

            tmp_in_1["set"] = si

            # set2

            tmp_in = pd.DataFrame(self.input_data["set_2"]["statistics"][sets][si])
            tmp_in = tmp_in[tmp_in[test_string] <= p_val]
            tmp_in[test_string] = (
                tmp_in[test_string]
                + np.min(tmp_in[test_string][tmp_in[test_string] != 0]) / 2
            )
            tmp_in["-log(p-val)"] = -np.log(tmp_in[test_string])

            tmp_in_2 = tmp_in.reset_index(drop=True)

            terms = list(
                metadata["term"][
                    (metadata["regulation"] == "s2")
                    | (metadata["regulation"] == "equal")
                ]
            )

            tmp_in_2 = tmp_in_2[tmp_in_2["specificity"].isin(terms)]

            tmp_in_2["set"] = si

            full_df_1 = pd.concat([pd.DataFrame(full_df_1), pd.DataFrame(tmp_in_1)])
            full_df_2 = pd.concat([pd.DataFrame(full_df_2), pd.DataFrame(tmp_in_2)])

        ##############################################################################

        if stat.upper() == "perc".upper():
            val = "pct"
        elif stat.upper() == "p_val".upper():
            val = "-log(p-val)"
        else:
            val = "n"

        plot_bin_data = self.create_inter_df(
            data_1=full_df_1,
            data_2=full_df_2,
            group_by="specificity",
            values=val,
            set_col="set",
        )

        plot = self.bivector_column(
            plot_bin_data=plot_bin_data,
            bin_value=stat,
            name_col="specificity",
            set_col="set",
            min_n=min_terms,
            n_max=n,
            width=width,
            bar_width=bar_width,
            selected_set=selected_set,
            inter_focus=False,
            s1_color="bisque",
            s2_color="wheat",
            sep_factor=sep_factor,
        )

        ##############################################################################

        return plot

    def diff_GOPa_network_create(
        self,
        data_set: str = "GO-TERM",
        genes_inc: int = 10,
        gene_int: bool = True,
        genes_only: bool = True,
        min_con: int = 2,
        children_con: bool = False,
        include_childrend: bool = True,
        selected_parents: list = [],
        selected_genes: list = [],
    ):

        GOPa_diff = pd.DataFrame(self.input_data["networks"][data_set])

        GOPa = pd.DataFrame(self.input_data["networks"][data_set])
        genes_list = list(set(GOPa["features"]))

        if len(selected_genes) > 0:
            to_select_genes = []
            for p in selected_genes:
                if p in list(GOPa["features"]):
                    to_select_genes.append(p)
                else:
                    print("\nCould not find {p} gene!")

            if len(to_select_genes) != 0:
                GOPa = GOPa[GOPa["features"].isin(to_select_genes)]
                genes_inc = max(genes_inc, len(to_select_genes))
            else:
                print("\nCould not use provided set of genes!")

        if data_set in ["GO-TERM", "KEGG", "REACTOME"]:

            GOPa_drop = GOPa[["parent", "children"]].drop_duplicates()

            GOPa_drop = Counter(list(GOPa_drop["parent"]))

            GOPa_drop = pd.DataFrame(GOPa_drop.items(), columns=["GOPa", "n"])

            GOPa_drop = list(GOPa_drop["GOPa"][GOPa_drop["n"] >= min_con])

            GOPa = GOPa[GOPa["parent"].isin(GOPa_drop)]

            del GOPa_drop

            if genes_inc > 0:

                genes_list = GOPa["features"]

                inter = None
                tmp_genes_list = []

                if gene_int:
                    inter = pd.DataFrame(self.input_data["GI"])
                    inter = inter[inter["A"] != inter["B"]]
                    inter = inter[inter["A"].isin(genes_list)]
                    inter = inter[inter["B"].isin(genes_list)]
                    tmp_genes_list = list(set(list(inter["B"]) + list(inter["A"])))

                    if len(tmp_genes_list) > 0:
                        genes_list = tmp_genes_list

                genes_list = Counter(genes_list)

                genes_list = pd.DataFrame(genes_list.items(), columns=["features", "n"])

                genes_list = genes_list.sort_values("n", ascending=False)

                gene_GOPa_p = GOPa[["parent", "features"]][
                    GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
                ]
                gene_GOP_c = GOPa[["features", "children"]][
                    GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
                ]
                genes_list = list(genes_list["features"][:genes_inc])

                if genes_only:
                    GOPa = GOPa[GOPa["features"].isin(genes_list)]

                gene_GOPa_p.columns = ["parent", "children"]

                gene_GOPa_p["color"] = "gray"

                GOPa = pd.concat([GOPa[["parent", "children", "color"]], gene_GOPa_p])

                if len(tmp_genes_list) > 0:
                    if isinstance(inter, pd.DataFrame):
                        inter = inter[inter["A"].isin(genes_list)]
                        inter = inter[inter["B"].isin(genes_list)]
                        inter = inter[["A", "B"]]
                        inter.columns = ["parent", "children"]
                        inter["color"] = "red"

                        GOPa = pd.concat([GOPa, inter])

                if children_con:

                    gene_GOP_c.columns = ["parent", "children"]

                    gene_GOP_c["color"] = "gray"

                    GOPa = pd.concat(
                        [GOPa[["parent", "children", "color"]], gene_GOP_c]
                    )

                del gene_GOP_c, gene_GOPa_p

            gopa_list = list(GOPa["parent"]) + list(GOPa["children"])

            gopa_list = Counter(gopa_list)

            gopa_list = pd.DataFrame(gopa_list.items(), columns=["GOPa", "weight"])

            if len(selected_parents) > 0:
                to_select = []
                to_select_genes = []

                for p in selected_parents:
                    if p in list(GOPa["parent"]):
                        to_select.append(p)
                        t = list(GOPa["children"][GOPa["parent"] == p])
                        for i in t:
                            tg = [x for x in genes_list if x in list(GOPa["children"])]
                            if i in tg:
                                to_select_genes.append(i)

                    else:
                        print("\nCould not find {p} parent term!")

                if len(to_select) != 0:
                    GOPa = GOPa[
                        GOPa["parent"].isin(to_select + to_select_genes)
                        & GOPa["children"].isin(
                            list(GOPa["children"][GOPa["parent"].isin(to_select)])
                        )
                    ]
                    gopa_list = gopa_list[
                        gopa_list["GOPa"].isin(
                            list(GOPa["parent"]) + list(GOPa["children"])
                        )
                    ]

                else:
                    print("\nCould not use provided set of parent terms!")

            if include_childrend is False:
                GOPa = GOPa[GOPa["children"].isin(list(GOPa["parent"]) + genes_list)]
                gopa_list = gopa_list[
                    gopa_list["GOPa"].isin(list(GOPa["parent"]) + genes_list)
                ]

            G = nx.Graph()

            s1_genes = list(
                self.input_data["set_1"]["enrichment"]["gene_info"]["found_names"]
            )
            s2_genes = list(
                self.input_data["set_2"]["enrichment"]["gene_info"]["found_names"]
            )

            s1_terms_parent = list(set(GOPa_diff["parent"][GOPa_diff["set"] == "s1"]))
            s2_terms_parent = list(set(GOPa_diff["parent"][GOPa_diff["set"] == "s2"]))
            inter_terms_parent = list(
                set(GOPa_diff["parent"][GOPa_diff["set"] == "inter"])
            )

            s1_terms_children = list(
                set(GOPa_diff["children"][GOPa_diff["set"] == "s1"])
            )
            s2_terms_children = list(
                set(GOPa_diff["children"][GOPa_diff["set"] == "s2"])
            )
            inter_terms_children = list(
                set(GOPa_diff["children"][GOPa_diff["set"] == "inter"])
            )

            for _, row in gopa_list.iterrows():
                node = row["GOPa"]

                if node in s1_genes:
                    color = "turquoise"
                    weight = np.log2(row["weight"] * 1000)

                elif node in s2_genes:
                    color = "mediumblue"
                    weight = np.log2(row["weight"] * 1000)

                elif node in s1_terms_parent:
                    color = "orangered"
                    weight = np.log2(row["weight"] * 1000) * 2

                elif node in s2_terms_parent:
                    color = "royalblue"
                    weight = np.log2(row["weight"] * 1000) * 2

                elif node in inter_terms_parent:
                    color = "gold"
                    weight = np.log2(row["weight"] * 1000) * 2

                elif node in s1_terms_children:
                    color = "gray"
                    weight = np.log2(row["weight"] * 1000)

                elif node in s2_terms_children:
                    color = "tan"
                    weight = np.log2(row["weight"] * 1000)

                elif node in inter_terms_children:
                    color = "lightgray"
                    weight = np.log2(row["weight"] * 1000)

                G.add_node(node, size=weight, color=color)

            for _, row in GOPa.iterrows():
                source = row["parent"]
                target = row["children"]
                color = row["color"]
                G.add_edge(source, target, color=color)

            return G

        else:

            print("\nWrong data set selected!")
            print("\nAvaiable data sets are included in:")

            for i in ["GO-TERM", "KEGG", "DISEASES", "ViMIC", "REACTOME"]:
                print(f"\n{i}")

    def diff_GI_network_create(self, min_con: int = 2):

        inter = pd.DataFrame(self.input_data["GI"])
        inter = inter[["A", "B", "connection_type"]]

        dict_meta = pd.DataFrame(
            {
                "interactions": [
                    ["gene -> gene"],
                    ["protein -> protein"],
                    ["gene -> protein"],
                    ["protein -> gene"],
                    ["gene -> gene", "protein -> protein"],
                    ["gene -> gene", "gene -> protein"],
                    ["gene -> gene", "protein -> gene"],
                    ["protein -> protein", "gene -> protein"],
                    ["protein -> protein", "protein -> gene"],
                    ["gene -> protein", "protein -> gene"],
                    ["gene -> gene", "protein -> protein", "gene -> protein"],
                    ["gene -> gene", "protein -> protein", "protein -> gene"],
                    ["gene -> gene", "gene -> protein", "protein -> gene"],
                    ["protein -> protein", "gene -> protein", "protein -> gene"],
                    [
                        "gene -> gene",
                        "protein -> protein",
                        "gene -> protein",
                        "protein -> gene",
                    ],
                ],
                "color": [
                    "#f67089",
                    "#f47832",
                    "#ca9213",
                    "#ad9d31",
                    "#8eb041",
                    "#4fb14f",
                    "#33b07a",
                    "#35ae99",
                    "#36acae",
                    "#38a9c5",
                    "#3aa3ec",
                    "#957cf4",
                    "#cd79f4",
                    "#f35fb5",
                    "#f669b7",
                ],
            }
        )

        genes_list = list(inter["A"]) + list(inter["B"])

        genes_list = Counter(genes_list)

        genes_list = pd.DataFrame(genes_list.items(), columns=["features", "n"])

        genes_list = genes_list.sort_values("n", ascending=False)

        genes_list = genes_list[genes_list["n"] >= min_con]

        inter = inter[inter["A"].isin(list(genes_list["features"]))]
        inter = inter[inter["B"].isin(list(genes_list["features"]))]

        inter = inter.groupby(["A", "B"]).agg({"connection_type": list}).reset_index()

        inter["color"] = "black"

        for inx in inter.index:
            for inx2 in dict_meta.index:
                if set(inter["connection_type"][inx]) == set(
                    dict_meta["interactions"][inx2]
                ):
                    inter["color"][inx] = dict_meta["color"][inx2]
                    break

        G = nx.Graph()

        s1_genes = list(
            self.input_data["set_1"]["enrichment"]["gene_info"]["found_names"]
        )
        s2_genes = list(
            self.input_data["set_2"]["enrichment"]["gene_info"]["found_names"]
        )

        for _, row in genes_list.iterrows():
            node = row["features"]

            if node in s1_genes:
                color = "orangered"
            elif node in s2_genes:
                color = "royalblue"
            weight = np.log2(row["n"] * 500)
            G.add_node(node, size=weight, color=color)

        for _, row in inter.iterrows():
            source = row["A"]
            target = row["B"]
            color = row["color"]
            G.add_edge(source, target, color=color)

        return G

    def diff_AUTO_ML_network(
        self,
        genes_inc: int = 10,
        gene_int: bool = True,
        genes_only: bool = True,
        min_con: int = 2,
        children_con: bool = False,
        include_childrend: bool = False,
        selected_parents: list = [],
        selected_genes: list = [],
    ):

        input_data = self.input_data

        full_genes = []
        genes_sets = []
        GOPa = pd.DataFrame()
        for s in ["GO-TERM", "KEGG", "REACTOME"]:
            if s in input_data["networks"].keys():
                genes_sets.append(set(input_data["networks"][s]["features"]))
                full_genes += list(set(input_data["networks"][s]["features"]))
                tmp = pd.DataFrame(input_data["networks"][s])
                tmp["source"] = s
                tmp["color"] = "gray"
                GOPa = pd.concat([GOPa, tmp])

        GOPa_diff = GOPa.copy()

        common_elements = set.intersection(*genes_sets)

        del genes_sets

        inter = pd.DataFrame(input_data["GI"])
        inter = inter[inter["A"].isin(full_genes)]
        inter = inter[inter["B"].isin(full_genes)]

        if len(common_elements) > 0:
            inter = inter[
                inter["A"].isin(common_elements) | inter["B"].isin(common_elements)
            ]

        selection_list = list(set(list(set(inter["B"])) + list(set(inter["A"]))))

        if len(selected_genes) > 0:
            to_select_genes = []
            for p in selected_genes:
                if p in list(GOPa["features"]):
                    to_select_genes.append(p)
                else:
                    print("\nCould not find {p} gene!")

            if len(to_select_genes) != 0:
                GOPa = GOPa[GOPa["features"].isin(to_select_genes)]
                genes_inc = max(genes_inc, len(to_select_genes))

            else:
                print("\nCould not use provided set of genes!")

        else:
            GOPa = GOPa[GOPa["features"].isin(selection_list)]

        GOPa_drop = GOPa[["parent", "children"]].drop_duplicates()

        GOPa_drop = Counter(list(GOPa_drop["parent"]))

        GOPa_drop = pd.DataFrame(GOPa_drop.items(), columns=["GOPa", "n"])

        GOPa_drop = list(GOPa_drop["GOPa"][GOPa_drop["n"] >= min_con])

        GOPa = GOPa[GOPa["parent"].isin(GOPa_drop)]

        del GOPa_drop

        if genes_inc > 0:

            genes_list = GOPa["features"]

            inter = None
            tmp_genes_list = []

            if gene_int:
                inter = pd.DataFrame(input_data["GI"])
                inter = inter[inter["A"] != inter["B"]]
                inter = inter[inter["A"].isin(genes_list)]
                inter = inter[inter["B"].isin(genes_list)]
                tmp_genes_list = list(set(list(inter["B"]) + list(inter["A"])))

                if len(tmp_genes_list) > 0:
                    genes_list = tmp_genes_list

            genes_list = Counter(genes_list)

            genes_list = pd.DataFrame(genes_list.items(), columns=["features", "n"])

            genes_list = genes_list.sort_values("n", ascending=False)

            gene_GOPa_p = GOPa[["parent", "features", "source", "color"]][
                GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
            ]
            gene_GOP_c = GOPa[["features", "children", "source", "color"]][
                GOPa["features"].isin(list(genes_list["features"][:genes_inc]))
            ]
            genes_list = list(genes_list["features"][:genes_inc])

            if genes_only:
                GOPa = GOPa[GOPa["features"].isin(genes_list)]

            gene_GOPa_p.columns = ["parent", "children", "source", "color"]

            GOPa = pd.concat(
                [GOPa[["parent", "children", "source", "color"]], gene_GOPa_p]
            )

            if len(tmp_genes_list) > 0:
                if isinstance(inter, pd.DataFrame):
                    inter = inter[inter["A"].isin(genes_list)]
                    inter = inter[inter["B"].isin(genes_list)]
                    inter = inter[["A", "B"]]
                    inter.columns = ["parent", "children"]
                    inter["source"] = "gene"
                    inter["color"] = "red"

                    GOPa = pd.concat([GOPa, inter])

            if children_con:

                gene_GOP_c.columns = ["parent", "children", "source", "color"]

                GOPa = pd.concat(
                    [GOPa[["parent", "children", "source", "color"]], gene_GOP_c]
                )

            del gene_GOP_c, gene_GOPa_p

        gopa_list = list(GOPa["parent"]) + list(GOPa["children"])

        gopa_list = Counter(gopa_list)

        gopa_list = pd.DataFrame(
            gopa_list.items(), columns=["GOPa", "weight"]
        ).reset_index(drop=True)

        gopa_list["source"] = None

        for inx in gopa_list.index:
            if gopa_list["GOPa"][inx] in list(GOPa["parent"]):
                gopa_list["source"][inx] = list(
                    GOPa["source"][GOPa["parent"] == gopa_list["GOPa"][inx]]
                )[0]
            elif gopa_list["GOPa"][inx] in list(GOPa["children"]):
                gopa_list["source"][inx] = list(
                    GOPa["source"][GOPa["children"] == gopa_list["GOPa"][inx]]
                )[0]

        if len(selected_parents) > 0:
            to_select = []
            to_select_genes = []

            for p in selected_parents:
                if p in list(GOPa["parent"]):
                    to_select.append(p)
                    t = list(GOPa["children"][GOPa["parent"] == p])
                    for i in t:
                        tg = [x for x in genes_list if x in list(GOPa["children"])]
                        if i in tg:
                            to_select_genes.append(i)

                else:
                    print("\nCould not find {p} parent term!")

            if len(to_select) != 0:
                GOPa = GOPa[
                    GOPa["parent"].isin(to_select + to_select_genes)
                    & GOPa["children"].isin(
                        list(GOPa["children"][GOPa["parent"].isin(to_select)])
                    )
                ]
                gopa_list = gopa_list[
                    gopa_list["GOPa"].isin(
                        list(GOPa["parent"]) + list(GOPa["children"])
                    )
                ]

            else:
                print("\nCould not use provided set of parent terms!")

        if include_childrend is False:
            GOPa = GOPa[GOPa["children"].isin(list(GOPa["parent"]) + genes_list)]
            gopa_list = gopa_list[
                gopa_list["GOPa"].isin(list(GOPa["parent"]) + genes_list)
            ]

        G = nx.Graph()

        s1_genes = list(
            self.input_data["set_1"]["enrichment"]["gene_info"]["found_names"]
        )
        s2_genes = list(
            self.input_data["set_2"]["enrichment"]["gene_info"]["found_names"]
        )

        s1_terms_parent = list(set(GOPa_diff["parent"][GOPa_diff["set"] == "s1"]))
        s2_terms_parent = list(set(GOPa_diff["parent"][GOPa_diff["set"] == "s2"]))
        inter_terms_parent = list(set(GOPa_diff["parent"][GOPa_diff["set"] == "inter"]))

        s1_terms_children = list(set(GOPa_diff["children"][GOPa_diff["set"] == "s1"]))
        s2_terms_children = list(set(GOPa_diff["children"][GOPa_diff["set"] == "s2"]))
        inter_terms_children = list(
            set(GOPa_diff["children"][GOPa_diff["set"] == "inter"])
        )

        for _, row in gopa_list.iterrows():
            node = row["GOPa"]

            if node in s1_genes:
                color = "turquoise"
                weight = np.log2(row["weight"] * 1000)

            elif node in s2_genes:
                color = "mediumblue"
                weight = np.log2(row["weight"] * 1000)

            elif node in s1_terms_parent:
                color = "orangered"
                weight = np.log2(row["weight"] * 1000) * 2

            elif node in s2_terms_parent:
                color = "royalblue"
                weight = np.log2(row["weight"] * 1000) * 2

            elif node in inter_terms_parent:
                color = "gold"
                weight = np.log2(row["weight"] * 1000) * 2

            elif node in s1_terms_children:
                color = "gray"
                weight = np.log2(row["weight"] * 1000)

            elif node in s2_terms_children:
                color = "tan"
                weight = np.log2(row["weight"] * 1000)

            elif node in inter_terms_children:
                color = "lightgray"
                weight = np.log2(row["weight"] * 1000)

            G.add_node(node, size=weight, color=color)

        for _, row in GOPa.iterrows():
            source = row["parent"]
            target = row["children"]
            color = row["color"]
            G.add_edge(source, target, color=color)

        return G

    def diff_gene_scatter(
        self,
        set_num=1,
        colors="viridis",
        species="human",
        hclust="complete",
        img_width=None,
        img_high=None,
        label_size=None,
        x_lab="Genes",
        legend_lab="log(TPM + 1)",
        selected_list: list = [],
    ):
        """
        This function creates a graph in the format of a scatter plot for expression data prepared in data frame format.

        Args:
            data (data frame) - data frame of genes/protein expression where on row are the gene/protein names and on column grouping variable (tissue / cell / ect. names)
            color (str) - palette color available for matplotlib in python eg. viridis
            species (str) - species for upper() or lower() letter for gene/protein name depending on
            hclust (str) - type of data clustering of input expression data eg. complete or None if  no clustering
            img_width (float) - width of the image or None for auto-adjusting
            img_high (float) - high of the image or None for auto-adjusting
            label_size (float) - labels size of the image or None for auto-adjusting
            x_lab (str) - tex for x axis label
            legend_lab (str) - description for legend label


        Returns:
            graph: Scatter plot of expression data
        """

        input_data_1 = self.input_data["set_1"]["enrichment"]["RNA-SEQ"]
        input_data_2 = self.input_data["set_2"]["enrichment"]["RNA-SEQ"]

        for i in input_data_1.keys():
            for i2 in input_data_1[i].keys():
                if i2 != "tissue":
                    input_data_2[i][i2] = input_data_1[i][i2]

        input_data = input_data_2

        del input_data_1, input_data_2

        return_dict = {}

        for i in input_data.keys():
            data = pd.DataFrame(input_data[i])
            data.index = data["tissue"]
            data.pop("tissue")

            if len(selected_list) > 0:
                selected_list = [y.upper() for y in selected_list]
                to_select = [x for x in data.columns if x.upper() in selected_list]
                data = data.loc[:, to_select]

            scatter_df = data

            if img_width is None:
                img_width = len(scatter_df.columns) * 1.2

            if img_high is None:
                img_high = len(scatter_df.index) * 0.9

            if label_size is None:
                label_size = np.log(len(scatter_df.index) * len(scatter_df.index)) * 2.5

                if label_size < 7:
                    label_size = 7

            cm = 1 / 2.54

            if len(scatter_df) > 1:

                Z = linkage(scatter_df, method=hclust)

                order_of_features = dendrogram(Z, no_plot=True)["leaves"]

                indexes_sort = list(scatter_df.index)
                sorted_list_rows = []
                for n in order_of_features:
                    sorted_list_rows.append(indexes_sort[n])

                scatter_df = scatter_df.transpose()

                Z = linkage(scatter_df, method=hclust)

                order_of_features = dendrogram(Z, no_plot=True)["leaves"]

                indexes_sort = list(scatter_df.index)
                sorted_list_columns = []
                for n in order_of_features:
                    sorted_list_columns.append(indexes_sort[n])

                scatter_df = scatter_df.transpose()

                scatter_df = scatter_df.loc[sorted_list_rows, sorted_list_columns]

            scatter_df = np.log(scatter_df + 1)
            scatter_df[scatter_df <= np.mean(scatter_df.quantile(0.10))] = (
                np.mean(np.mean(scatter_df, axis=1)) / 10
            )

            if species.lower() == "human":
                scatter_df.index = [x.upper() for x in scatter_df.index]
            else:
                scatter_df.index = [x.title() for x in scatter_df.index]

            scatter_df.insert(0, "  ", 0)

            scatter_df[" "] = 0

            fig, ax = plt.subplots(figsize=(img_width * cm, img_high * cm))

            plt.scatter(
                x=[*range(0, len(scatter_df.columns), 1)],
                y=[" "] * len(scatter_df.columns),
                s=0,
                cmap=colors,
                edgecolors=None,
            )

            for index, row in enumerate(scatter_df.index):
                x = [*range(0, len(np.array(scatter_df.loc[row,])), 1)]
                y = [row] * len(x)
                s = np.array(scatter_df.loc[row,])
                plt.scatter(
                    x,
                    y,
                    s=np.log(s + 1) * 70,
                    c=s,
                    cmap=colors,
                    edgecolors="black",
                    vmin=np.array(scatter_df).min(),
                    vmax=np.array(scatter_df).max(),
                    linewidth=0.00001,
                )
                sm = plt.cm.ScalarMappable(cmap=colors)
                sm.set_clim(
                    vmin=np.array(scatter_df).min(), vmax=np.array(scatter_df).max()
                )
                plt.xticks(x, scatter_df.columns)
                plt.ylabel(str(x_lab), fontsize=label_size)

            plt.scatter(
                x=[*range(0, len(scatter_df.columns), 1)],
                y=[""] * len(scatter_df.columns),
                s=0,
                cmap=colors,
                edgecolors=None,
            )

            plt.xticks(rotation=80)
            plt.tight_layout()
            plt.margins(0.005)
            plt.xticks(fontsize=label_size)
            plt.yticks(fontsize=label_size)

            len_bar = ax.get_position().height / 5
            if len(scatter_df) < 15:
                len_bar = 0.65

                cbar = fig.colorbar(sm, ax=ax)
                cbar.ax.set_ylabel(str(legend_lab), fontsize=label_size * 0.9)
                cbar.ax.yaxis.set_ticks_position("right")
                cbar.ax.set_position(
                    [
                        ax.get_position().x1 + 0.05,
                        (ax.get_position().y0 + ax.get_position().y1) / 1.9,
                        ax.get_position().width / 0.05,
                        len_bar,
                    ]
                )
                cbar.ax.yaxis.set_label_position("right")
                cbar.ax.yaxis.set_tick_params(labelsize=label_size * 0.8)
                cbar.outline.set_edgecolor("none")
            else:
                cbar = fig.colorbar(sm, ax=ax)
                cbar.ax.set_ylabel(str(legend_lab), fontsize=label_size * 0.9)
                cbar.ax.yaxis.set_ticks_position("right")
                cbar.ax.set_position(
                    [
                        ax.get_position().x1 + 0.05,
                        (ax.get_position().y0 + ax.get_position().y1) / 1.45,
                        ax.get_position().width / 0.05,
                        len_bar,
                    ]
                )
                cbar.ax.yaxis.set_label_position("right")
                cbar.ax.yaxis.set_tick_params(labelsize=label_size * 0.8)
                cbar.outline.set_edgecolor("none")

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["bottom"].set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.xaxis.set_tick_params(length=0, labelbottom=True)
            ax.yaxis.set_tick_params(length=0, labelbottom=True)
            ax.grid(False)

            if self.show_plot:
                plt.show()
            elif self.show_plot is False:
                plt.close(fig)

            return_dict[i] = fig

        return return_dict

    def diff_gene_type_plot(
        self,
        set1_name: str = "Set 1",
        set2_name: str = "Set 2",
        image_width=12,
        image_high=6,
        font_size=15,
    ):
        """
        This method generates a pie chart visualizing the distribution of gene types based on set1 and set2 enrichment data.

        Args:
            set1_name (str) - name for the set1 data. Default is 'Set 1',
            set2_name (str) - name for the set2 data. Default is 'Set 2',
            image_width (int) - width of the plot in inches. Default is 12
            image_high (int) - height of the plot in inches. Default is 6
            font_size (int) - font size. Default is 15

        Returns:
            fig (matplotlib.figure.Figure) - figure object containing a pie chart that visualizes the distribution of gene type occurrences as percentages
        """

        tmp_info = self.input_data["set_1"]["enrichment"]["gene_info"]

        sp = self.input_data["set_1"]["enrichment"]["species"]["species_genes"]

        h_genes = []
        m_genes = []
        r_genes = []

        if "Homo sapiens" in sp:

            h_genes = tmp_info["gen_type_Homo_sapiens"]

        if "Mus musculus" in sp:

            m_genes = tmp_info["gen_type_Mus_musculus"]

        if "Rattus norvegicus" in sp:

            r_genes = tmp_info["gen_type_Rattus_norvegicus"]

        full_genes = []
        for i in range(len(tmp_info["sid"])):
            g = []

            if len(h_genes) > 0:
                if isinstance(h_genes[i], list):
                    g += h_genes[i]
                elif h_genes[i] is None:
                    g += []
                else:
                    g.append(h_genes[i])

            if len(m_genes) > 0:
                if isinstance(m_genes[i], list):
                    g += m_genes[i]
                elif m_genes[i] is None:
                    g += []
                else:
                    g.append(m_genes[i])

            if len(r_genes) > 0:
                if isinstance(r_genes[i], list):
                    g += r_genes[i]
                elif r_genes[i] is None:
                    g += []
                else:
                    g.append(r_genes[i])

            if len(g) == 0:
                g = ["undefined"]

            full_genes += list(set(g))

        cmap = "summer"

        count_gene = Counter(full_genes)

        count_gene = pd.DataFrame(count_gene.items(), columns=["gene_type", "n"])

        count_gene["pct"] = (count_gene["n"] / sum(count_gene["n"])) * 100

        count_gene["pct"] = [round(x, 2) for x in count_gene["pct"]]

        count_gene = count_gene.sort_values("n", ascending=False)

        count_gene1 = count_gene.reset_index(drop=True)

        labels1 = (
            count_gene1["gene_type"]
            + [" : "] * len(count_gene1["gene_type"])
            + count_gene1["pct"].astype(str)
            + ["%"] * len(count_gene1["gene_type"])
        )

        cn = len(count_gene["gene_type"])

        existing_cmap = plt.get_cmap(cmap)

        colors = [existing_cmap(i / cn) for i in range(cn)]

        colordf1 = pd.DataFrame({"color": colors, "label": labels1})

        #######################################################################

        tmp_info = self.input_data["set_2"]["enrichment"]["gene_info"]

        sp = self.input_data["set_2"]["enrichment"]["species"]["species_genes"]

        h_genes = []
        m_genes = []
        r_genes = []

        if "Homo sapiens" in sp:

            h_genes = tmp_info["gen_type_Homo_sapiens"]

        if "Mus musculus" in sp:

            m_genes = tmp_info["gen_type_Mus_musculus"]

        if "Rattus norvegicus" in sp:

            r_genes = tmp_info["gen_type_Rattus_norvegicus"]

        full_genes = []
        for i in range(len(tmp_info["sid"])):
            g = []

            if len(h_genes) > 0:
                if isinstance(h_genes[i], list):
                    g += h_genes[i]
                elif h_genes[i] is None:
                    g += []
                else:
                    g.append(h_genes[i])

            if len(m_genes) > 0:
                if isinstance(m_genes[i], list):
                    g += m_genes[i]
                elif m_genes[i] is None:
                    g += []
                else:
                    g.append(m_genes[i])

            if len(r_genes) > 0:
                if isinstance(r_genes[i], list):
                    g += r_genes[i]
                elif r_genes[i] is None:
                    g += []
                else:
                    g.append(r_genes[i])

            if len(g) == 0:
                g = ["undefined"]

            full_genes += list(set(g))

        cmap = "autumn"

        count_gene = Counter(full_genes)

        count_gene = pd.DataFrame(count_gene.items(), columns=["gene_type", "n"])

        count_gene["pct"] = (count_gene["n"] / sum(count_gene["n"])) * 100

        count_gene["pct"] = [round(x, 2) for x in count_gene["pct"]]

        count_gene = count_gene.sort_values("n", ascending=False)

        count_gene2 = count_gene.reset_index(drop=True)

        labels2 = (
            count_gene2["gene_type"]
            + [" : "] * len(count_gene2["gene_type"])
            + count_gene2["pct"].astype(str)
            + ["%"] * len(count_gene2["gene_type"])
        )

        cn = len(count_gene["gene_type"])

        existing_cmap = plt.get_cmap(cmap)

        colors = [existing_cmap(i / cn) for i in range(cn)]

        colordf2 = pd.DataFrame({"color": colors, "label": labels2})

        #######################################################################

        fig, (ax1, ax2) = plt.subplots(
            1, 2, figsize=(image_width, image_high), subplot_kw=dict(aspect="equal")
        )

        wedges1, _ = ax1.pie(
            count_gene1["pct"],
            startangle=90,
            labeldistance=1.05,
            colors=[
                colordf1["color"][colordf1["label"] == x][
                    colordf1.index[colordf1["label"] == x][0]
                ]
                for x in labels1
            ],
            wedgeprops={"linewidth": 0.5, "edgecolor": "black"},
        )

        kw = dict(arrowprops=dict(arrowstyle="-"), zorder=0, va="center")
        n = 0
        for i, p in enumerate(wedges1):
            ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={ang}"
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            if len(labels1[i]) > 0:
                n += 0.45
                ax1.annotate(
                    labels1[i],
                    xy=(x, y),
                    xytext=(1.4 * x + (n * x / 4), y * 1.1 + (n * y / 4)),
                    horizontalalignment=horizontalalignment,
                    fontsize=font_size,
                    weight="bold",
                    **kw,
                )

        ax1.text(
            0.5,
            0.5,
            f"{set1_name}\nGene type",
            transform=ax1.transAxes,
            va="center",
            ha="center",
            backgroundcolor="white",
            weight="bold",
            fontsize=int(font_size) * 1.1,
        )

        wedges2, _ = ax2.pie(
            count_gene2["pct"],
            startangle=90,
            labeldistance=1.05,
            colors=[
                colordf2["color"][colordf2["label"] == x][
                    colordf2.index[colordf2["label"] == x][0]
                ]
                for x in labels2
            ],
            wedgeprops={"linewidth": 0.5, "edgecolor": "black"},
        )

        kw = dict(arrowprops=dict(arrowstyle="-"), zorder=0, va="center")
        n = 0
        for i, p in enumerate(wedges2):
            ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={ang}"
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            if len(labels2[i]) > 0:
                n += 0.45
                ax2.annotate(
                    labels2[i],
                    xy=(x, y),
                    xytext=(1.4 * x + (n * x / 4), y * 1.1 + (n * y / 4)),
                    horizontalalignment=horizontalalignment,
                    fontsize=font_size,
                    weight="bold",
                    **kw,
                )

        ax2.text(
            0.5,
            0.5,
            f"{set2_name}\nGene type",
            transform=ax2.transAxes,
            va="center",
            ha="center",
            backgroundcolor="white",
            weight="bold",
            fontsize=int(font_size) * 1.1,
        )

        circle1 = plt.Circle(
            (0, 0),
            0.6,
            color="white",
            linewidth=1.5,
            edgecolor="black",
            transform=ax1.transData,
        )
        ax1.add_artist(circle1)

        circle2 = plt.Circle(
            (0, 0),
            0.6,
            color="white",
            linewidth=1.5,
            edgecolor="black",
            transform=ax2.transData,
        )
        ax2.add_artist(circle2)

        plt.tight_layout()

        if self.show_plot:
            plt.show()
        elif self.show_plot is False:
            plt.close(fig)

        return fig


def enrichment_heatmap(
    data: pd.DataFrame,
    stat_col: str,
    term_col: str,
    set_col: str,
    sets: dict | list | None = None,
    title: str = "",
    fig_size: tuple = (8, 10),
    font_size=14,
    scale: bool = False,
    clustering: str | None = "ward",
):
    """
    Generate an enrichment heatmap from statistical significance values
    (e.g. p-values) across multiple sets and terms.

    The function reshapes the input data into a term × set matrix, applies
    a -log10 transformation to the statistical values, optionally scales the
    data, performs hierarchical clustering on rows and columns, and visualizes
    the result using a seaborn heatmap.

    Args:
        data (pd.DataFrame) - DataFrame containing enrichment analysis results.
        stat_col (str) - name of the column containing statistical values (e.g. p-values).
        term_col (str) - name of the column containing term identifiers (e.g. pathways, GO terms).
        set_col (str) - name of the column specifying the set or group eg. cell_names / sample_names.
        sets (dict | list | None) - optional:
            Sets to include in the heatmap.
            - list: ensures presence of the specified sets,
            - dict: additionally renames columns (key → new name),
            - None: uses all sets found in the data.
        title (str) - label for the Y-axis (term description).
        fig_size (tuple) - figure size in inches (width, height).
        font_size (int) - base font size used in the plot.
        scale (bool) - default: False
            If True, values are scaled to the range [0, 1] using MinMaxScaler.
        clustering (str | None) - default 'ward'
            Hierarchical clustering method (e.g. 'ward', 'average', 'complete').
            If None, clustering is disabled.

    Returns:
        fig (matplotlib.figure.Figure) - figure object containing the heatmap.

    Raises:
        ValueError
            If duplicated (term, set) pairs are found in the input data.

    Notes:
        - Statistical values are transformed using -log10(p-value).
        - Missing term–set combinations are filled with zeros.
        - Row and column clustering are performed independently.
    """

    scale_label = "-log10(p_value)"

    data["-log(p_value)"] = -np.log10(data[stat_col])

    if data[[term_col, set_col]].duplicated().any():
        raise ValueError(f"Duplicated values occur in column: {term_col}")

    if isinstance(sets, dict):
        sets_list = list(set(sets.keys()))
    elif isinstance(sets, list):
        sets_list = list(sets)
    else:
        sets_list = None

    heatmap_data = data.pivot_table(
        index=term_col, columns=set_col, values="-log(p_value)", aggfunc="max"
    ).fillna(0)

    if sets_list is not None:
        if set(heatmap_data.columns) != set(sets_list):
            list_unvalid = [x for x in sets_list if x not in set(heatmap_data.columns)]
            for d in list_unvalid:
                heatmap_data[d] = 0

    if isinstance(sets, dict):
        heatmap_data = heatmap_data.rename(columns=sets)

    if scale:
        scale_label = f"scaled({scale_label})"
        scaler = MinMaxScaler()
        heatmap_data = pd.DataFrame(
            scaler.fit_transform(heatmap_data),
            index=heatmap_data.index,
            columns=heatmap_data.columns,
        )

    if clustering is not None:
        Z_rows = linkage(heatmap_data.values, method=clustering)
        row_order = leaves_list(Z_rows)

        Z_cols = linkage(heatmap_data.values.T, method=clustering)
        col_order = leaves_list(Z_cols)

        heatmap_data = heatmap_data.iloc[row_order, col_order]

    fig, ax = plt.subplots(figsize=fig_size)
    sns.heatmap(
        heatmap_data,
        ax=ax,
        cmap="viridis",
        linewidths=0.5,
        linecolor="gray",
        cbar_kws={"label": scale_label},
        fmt=".2f",
    )
    ax.set_xticks(np.arange(len(heatmap_data.columns)) + 0.5)
    ax.set_yticks(np.arange(len(heatmap_data.index)) + 0.5)
    ax.set_ylabel(title, fontsize=font_size)
    ax.set_xlabel("Set", fontsize=font_size)
    ax.set_xticklabels(
        ax.get_xticklabels(), rotation=90, ha="right", fontsize=font_size * 0.8
    )
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=font_size * 0.8)

    # colorbar fontsize
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=font_size * 0.8)

    plt.tight_layout()
    plt.show()

    return fig
