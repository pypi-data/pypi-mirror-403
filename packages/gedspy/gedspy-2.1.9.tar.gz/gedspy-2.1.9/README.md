# GEDSpy (Gene Enrichment for Drug Searching) - python library

![Python version](https://img.shields.io/badge/python-%E2%89%A53.12-blue?logo=python&logoColor=white.png) ![License](https://img.shields.io/badge/license-GPLv3-blue) ![Docs](https://img.shields.io/badge/docs-available-blueviolet)


#### GEDSpy is the python library for gene list enrichment with genes ontology, pathways, tissue & cell type specificity, genes interactions and cell connections

<p align="right">
<img  src="https://github.com/jkubis96/Logos/blob/main/logos/jbs_current.png?raw=true" alt="drawing" width="200" />
</p>


### Author: Jakub Kubiś 

<div align="left">
 Institute of Bioorganic Chemistry<br />
 Polish Academy of Sciences<br />
</div>


## Description




</br>


GEDSpy is a Python library designed for the analysis of biological data, particularly in high-throughput omics studies. It is a powerful tool for RNA-seq, single-cell RNA-seq, proteomics, and other large-scale biological analyses where numerous differentially expressed genes or proteins are identified. GEDSpy leverages multiple renowned biological databases to enhance functional analysis, pathway enrichment, and interaction studies. It integrates data from: Gene Ontology (A structured framework for gene function classification) , Kyoto Encyclopedia of Genes and Genomes (A resource for understanding high-level functions and utilities of biological systems), Reactome (A curated knowledge base of biological pathways), Human Protein Atlas (A comprehensive database of human protein expression), NCBI (A vast repository of genetic and biomedical data), STRING (A database of known and predicted protein-protein interactions), IntAct (A repository of molecular interaction data), CellTalk (A database for intercellular communication analysis), CellPhone (A tool for inferring cell-cell interactions from single-cell transcriptomics), Human Diseases (A resource linking genes to diseases), ViMic (A database for microbial virulence factors).

GEDSpy is designed to streamline biological data interpretation, enabling researchers to perform in-depth functional analyses, pathway enrichment, and drug target discovery. Its integration of multiple databases makes it an essential tool for translational research, biomarker identification, and disease mechanism exploration. 


<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/hu_mu_ra.jpg" alt="drawing" width="500" />
</p>


In this approach, the genomes of *Rattus norvegicus* and *Mus musculus* were integrated under the aegis of *Homo sapiens*, using reference genomes and data from NCBI. This unified genome served as a foundation for mapping data from all utilized datasets. Finally, dedicated algorithms for data analysis were developed and implemented as the GEDSpy library. This advancement simplifies translation studies between the most common animal models and *Homo sapiens*, facilitating both preclinical and clinical research.


</br>

Included data bases:

* [Gene Ontology (GO-TERM)](http://geneontology.org/)
* [KEGG (Kyoto Encyclopedia of Genes and Genomes)](https://www.genome.jp/kegg/)
* [Reactome](https://reactome.org/)
* [HPA (Human Protein Atlas)](https://www.proteinatlas.org/)
* [NCBI](https://www.ncbi.nlm.nih.gov/)
* [STRING](https://string-db.org/)
* [IntAct](https://www.ebi.ac.uk/intact/home)
* [CellTalk](https://tcm.zju.edu.cn/celltalkdb/)
* [CellPhone](https://www.cellphonedb.org/)
* [Human Diseases](https://diseases.jensenlab.org/Search)
* [ViMic](http://bmtongji.cn/ViMIC/index.php)


*If you use GEDSpy, please remember to cite both GEDSpy and the original sources of the data you utilized in your work.*

In the case of enrichment analysis, it is recommended to use the  [JVectorGraph](https://github.com/jkubis96/JVectorGraph) library to easily adjust and customise graph and network visualisations from the Python side.


<br />

## Table of contents

[Installation](#installation) \
[Usage](#usage)
1. [Enrichment](#enr) \
1.1 [Find features in GEDS database](#ffs) \
1.2 [Enrichment options](#eo)             
1.2.1 [Human Protein Atlas (HPA)](#hpa1) \
1.2.2 [Kyoto Encyclopedia of Genes and Genomes (KEGG)](#kegg1) \
1.2.3 [GeneOntology (GO-TERM)](#go1) \
1.2.4 [Reactome](#r1) \
1.2.5 [Human Diseases](#hd1) \
1.2.6 [Viral Diseases (ViMIC)](#vi1) \
1.2.7 [IntAct](#ia1) \
1.2.8 [STRING](#str1) \
1.2.9 [CellConnections](#cc1) \
1.2.10 [RNAseq of tissues](#rnaseq1) \
1.2.11 [Full Gene Set Enrichment](#fge1) 
2. [Single Gene Set Analysis (Analysis)](#ans2) \
2.1 [Set parameters](#sp2) \
2.1.1 [Interaction parameters](#ip2) \
2.1.2 [Network parameters](#np2) \
2.1.3 [GO-TERM gradation parameter](#gp2) \
2.2 [Overrepresentation analysis](#op2) \
2.2.1 [GO-TERM overrepresenation analysis](#gop2) \
2.2.2 [KEGG overrepresentation analysis](#kop2) \
2.2.3 [Reactome overrepresentation analysis](#rop2) \
2.2.4 [Viral diseases (ViMIC) overrepresentation analysis](#vdop2) \
2.2.5 [Human Diseases overrepresentation analysis](#hdop2) \
2.2.6 [Specificity (HPA) overrepresentation analysis](#sop2) \
2.3 [Gene Interactions (GI) analysis](#gi2) \
2.4 [Network analysis](#ni2) \
2.4.1 [Reactome network analysis](#rna2) \
2.4.2 [KEGG network analysis](#kna2) \
2.4.3 [GO-TERM network analysis](#gtna2) \
2.5 [Full enrichment data analysis](#feda2) 
3. [Single Gene Set Visualisation](#sgs3) \
3.1 [Gene type - pie chart](#gt3) \
3.2 [GO-TERMS - bar plot](#gtb3) \
3.3 [KEGG - bar plot](#kbp3) \
3.4 [Reactome - bar plot](#rbp3) \
3.5 [Specificity - bar plot](#sbp3) \
3.6 [Human Diseases - bar plot](#hbp3) \
3.7 [Viral Diseases (ViMIC) - bar plot](#vbp3) \
3.8 [Blood markers - bar plot](#bbp3) \
3.9 [GOPa - network](#gopa3) \
3.10 [Genes Interactions (GI) - network](#gipa3) \
3.11 [GOPa AutoML - network](#aml3) \
3.12 [RNAseq tissue - scatter plot](#rnaset3) 
4. [Differential Set Analysis (DSA)](#dsa4) \
4.1 [DSA - FC parameter](#dsaf4) \
4.2 [GO-TERM - DSA](#godsa4) \
4.3 [KEGG - DSA](#kodsa4) \
4.4 [Reactome - DSA](#rodsa4) \
4.5 [Specificity (HPA) - DSA](#sodsa4) \
4.6 [Genes Interactions (GI) - DSA](#gdsa4) \
4.7 [Network analysis - DSA](#nadsa4) \
4.8 [Inter CellConnection (ICC)](#iccdsa4) \
4.9 [Inter Terms (IT) - DSA](#itdsa4) \
4.10 [Full analysis - DSA](#fuldsa4) 
5. [Differential Set Analysis (DSA) Visualisation](#dsav5) \
5.1 [Both sets graphs](#dsav5b) \
5.1.1 [Gene type - pie chart](#gtdsav5) \
5.1.2 [GO-TERMS - bar plot](#godsav5) \
5.1.3 [KEGG - bar plot](#kdsav5) \
5.1.4 [Reactome - bar plot](#rdsav5) \
5.1.5 [Specificity - bar plot](#sdsav5) \
5.1.6 [Human Diseases - bar plot](#hdsav5) \
5.1.7 [Viral Diseases (ViMIC) - bar plot](#vdsav5) \
5.1.8 [GOPa - network](#gopasav5) \
5.1.9 [Genes Interactions (GI) - network](#gisav5) \
5.1.10 [GOPa AutoML - network](#gopaml5) \
5.1.11 [RNAseq tissue - scatter plot](#rnaseq5) \
5.1.12 [Adjusted Terms - Heatmap](#rnaseq6)

6. [GetRawData](#grd7) \
6.1 [Get combined genome](#gdcg6) \
6.2 [Get annotated RNAseq data](#gard6) \
6.3 [Get annotated Reactome data](#gare6) \
6.4 [Get annotated HPA data](#ghpa6) \
6.5 [Get annotated Human Diseases data](#gahd6) \
6.6 [Get annotated viral diseases (ViMIC) data](#gavm6) \
6.7 [Get annotated KEGG data](#gkeg6) \
6.8 [Get annotated GO-TERM data](#gago6) \
6.9 [Get annotated IntAct data](#gaia6) \
6.10 [Get annotated STRING data](#gast6) \
6.11 [Get adjusted CellTalk data](#gact6) \
6.12 [Get adjusted CellPhone data](#gacp6) \
6.13 [Get annotated CellInteraction data](#gaci6) 
7. [GetRawData](#grd7) \
7.1 [Get combined genome](#gdcg7) \
7.2 [Get RNAseq data](#gard7) \
7.3 [Get raw Reactome data](#gare7) \
7.4 [Get raw HPA data](#ghpa7) \
7.5 [Get raw Human Diseases data](#gahd7) \
7.6 [Get raw viral diseases (ViMIC) data](#gavm7) \
7.7 [Get raw KEGG data](#gkeg7) \
7.8 [Get raw GO-TERM data](#gago7) \
7.9 [Get raw IntAct data](#gaia7) \
7.10 [Get raw STRING data](#gast7) \
7.11 [Get raw CellTalk data](#gact7) \
7.12 [Get raw CellPhone data](#gacp7) 
8. [DataDownloading](#grd8) \
8.1 [Reference genome](#gdcg8) \
8.2 [RNAseq data](#gard8) \
8.3 [IntAct data](#gare8) \
8.4 [Human diseases data](#ghpa8) \
8.5 [Viral diseases data](#gahd8) \
8.6 [Human Protein Atlas - tissue / cell data](#gavm8) \
8.7 [STRING - interaction data](#gkeg8) \
8.8 [KEGG data](#gago8) \
8.9 [REACTOME data](#gaia8) \
8.10 [GO-TERM data](#gast8) \
8.11 [CellTalk data](#gact8) \
8.12 [CellPhone data](#gacp8) 
9. [UpdatePanel](#up9) \
9.1 [Check last update of data](#chlu9) \
9.2 [Update data from GEDSdb](#udfg9) \
9.3 [Update data from data sources](#udfs9) 
10. [Example enrichment analysis of single set](#ex10) 
11. [Example enrichment analysis of double sets](#ex11)

<br />

<br />


# Installation <a id="installation"></a>

#### In command line write:

```
pip install gedspy
```



<br />


# Usage <a id="usage"></a>

<br />

### 1. Enrichment<a id="enr"></a>

The data sets are annotated to the Ref_Genome (get_REF_GEN()) by ids

```
from gedspy import Enrichment

# initiate class
enr = Enrichment()
```



#### 1.1 Find features in GEDS database <a id="ffs"></a>

*  Homo sapiens / Mus musculus / Rattus norvegicus

```
enr.select_features(features_list)
```

    This method searches for the occurrence of genes or proteins in the GEDS database.  
    Available names include those from HGNC, Ensembl, or NCBI gene names or IDs,  
    for the species Homo sapiens, Mus musculus, or Rattus norvegicus.
        
        Args:
            features_list (list) - list of features (gene or protein names or IDs)
           
        Returns:
            Updates `self.genome` with feature information found in the GEDS database
<br />


#### 1.2 Enrichment options <a id="eo"></a>

##### 1.2.1 Human Protein Atlas (HPA) <a id="hpa1"></a>


```
enr.enriche_specificiti()
```

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
<br />

```
HPA_data = enr.get_HPA
```

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
        

<br />


##### 1.2.2 Kyoto Encyclopedia of Genes and Genomes (KEGG) <a id="kegg1"></a>


```
enr.enriche_KEGG()
```

    This method selects elements from the GEDS database that are included in the Kyoto Encyclopedia of Genes and Genomes (KEGG) information.  
     
        Returns:  
            Updates `self.KEGG` with KEGG information.  
            To retrieve the results, use the `self.get_KEGG` method.  
<br />

```
KEGG_data = enr.get_KEGG
```

    This method returns the Kyoto Encyclopedia of Genes and Genomes (KEGG) information.  
        
        Returns:  
            Returns `self.KEGG` with KEGG information enriched using the `self.enriche_KEGG` method.

<br />

##### 1.2.3 GeneOntology (GO-TERM) <a id="go1"></a>


```
enr.enriche_GOTERM()
```

    This method selects elements from the GEDS database that are included in the GeneOntology (GO-TERM) information.  
        
        Returns:  
            Updates `self.GO` with GO-TERM information.  
            To retrieve the results, use the `self.get_GO_TERM` method.  

<br />

```
GO_data = enr.get_GO_TERM
```


    This method returns the GeneOntology (GO-TERM) information.  
        
        Returns:  
            Returns `self.GO` with GeneOntology (GO-TERM) information enriched using the `self.enriche_GOTERM` method.
        
<br />

##### 1.2.4 Reactome <a id="r1"></a>


```
enr.enriche_REACTOME()
```

    This method selects elements from the GEDS database that are included in the Reactome information.  
        
        Returns:  
            Updates `self.REACTOME` with Reactome information.  
            To retrieve the results, use the `self.get_REACTOME` method.  

<br />

```
REACTOME_data = enr.get_REACTOME
```

    This method returns the Reactome information.  
        
        Returns:  
            Returns `self.REACTOME` with Reactome information enriched using the `self.enriche_REACTOME` method.

<br />

##### 1.2.5 Human Diseases <a id="hd1"></a>


```
enr.enriche_DISEASES()
```

    This method selects elements from the GEDS database that are included in the Human Diseases information.  
        
        Returns:  
            Updates `self.Diseases` with Human Diseases information.  
            To retrieve the results, use the `self.get_DISEASES` method. 

<br />

```
DISEASES_data = enr.get_DISEASES
```

    This method returns the Human Diseases information.  
        
        Returns:  
            Returns `self.Diseases` with Human Diseases information enriched using the `self.enriche_DISEASES` method.
        

<br />

##### 1.2.6 Viral Diseases (ViMIC) <a id="vi1"></a>


```
enr.enriche_ViMIC()
```

    This method selects elements from the GEDS database that are included in the Viral Diseases (ViMIC) information.  
        
        Returns:  
            Updates `self.ViMIC` with Viral Disease (ViMIC) information.  
            To retrieve the results, use the `self.get_ViMIC` method.  

<br />


```
ViMIC_data = enr.get_ViMIC
```

    This method returns the Viral Diseases (ViMIC) information.  
        
        Returns:  
            Returns `self.ViMIC` with Viral Diseases (ViMIC) information enriched using the `self.enriche_ViMIC` method.
        

<br />

##### 1.2.7 IntAct <a id="ia1"></a>


```
enr.enriche_IntAct()
```

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

<br />

```
IntAct_data = enr.get_IntAct
```

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

<br />

##### 1.2.8 STRING <a id="str1"></a>


```
enr.enriche_STRING()
```

    This method selects elements from the GEDS database that are included in the STRING information.  
        
        Returns:  
            Updates `self.STRING` with STRING information.  
            To retrieve the results, use the `self.get_STRING` method.  

<br />


```
STRING_data = enr.get_STRING
```

    This method returns the STRING information.  
        
        Returns:  
            Returns `self.STRING` with STRING information enriched using the `self.enriche_STRING` method.
        


<br />

##### 1.2.9 CellConnections <a id="cc1"></a>


```
enr.enriche_CellCon()
```

    This method selects elements from the GEDS database that are included in the CellPhone / CellTalk information.  
        
        Returns:  
            Updates `self.CellCon` with CellPhone / CellTalk information.  
            To retrieve the results, use the `self.get_CellCon` method. 


<br />


```
CellCon_data = enr.get_CellCon
```

    This method returns the CellPhone / CellTalk information.  
        
        Returns:  
            Returns `self.CellCon` with Human Protein Atlas information enriched using the `self.enriche_CellCon` method.
        

<br />


##### 1.2.10  RNAseq of tissues <a id="rnaseq1"></a>


```
enr.enriche_RNA_SEQ()
```

    This method selects elements from the GEDS database that are included in the RNAseq information.  
    It includes specificity to the following data sets:  
        -human_tissue_expression_HPA
        -human_tissue_expression_RNA_total_tissue
        -human_tissue_expression_fetal_development_circular

        Returns:  
            Updates `self.RNA_SEQ` with RNAseq information.  
            To retrieve the results, use the `self.get_RNA_SEQ` method.  


<br />


```
RNASEQ_data = enr.get_RNA_SEQ
```

    This method returns the RNAseq information.  
    It includes specificity to the following data sets:  
        -human_tissue_expression_HPA
        -human_tissue_expression_RNA_total_tissue
        -human_tissue_expression_fetal_development_circular
        
        Returns:  
            Returns `self.RNA_SEQ` with RNAseq information enriched using the `self.enriche_RNA_SEQ` method.
<br />



##### 1.2.11 Full Gene Set Enrichment <a id="fge1"></a>


```
enr.full_enrichment()
```

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


<br />


```
results = enr.get_results()
```

    This method returns the full enrichment analysis dictionary containing on keys:  
        - 'gene_info' - genome information for the selected gene set [see `self.get_gene_info` property]
        - 'HPA' - Human Protein Atlas (HPA) [see 'self.get_HPA' property]  
        - 'KEGG' - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see 'self.get_KEGG' property]  
        - 'GO-TERM' - GeneOntology (GO-TERM) [see 'self.get_GO_TERM' property]  
        - 'REACTOME' - Reactome [see 'self.get_REACTOME' property]  
        - 'DISEASES' - Human Diseases [see 'self.get_DISEASES' property]  
        - 'ViMIC' - Viral Diseases (ViMIC) [see 'self.get_ViMIC' property]  
        - 'IntAct' - IntAct [see 'self.get_IntAct' property]  
        - 'STRING' - STRING [see 'self.get_STRING' property]  
        - 'CellConnections' - CellConnections (CellPhone / CellTalk) [see 'self.get_CellCon' property]  
        - 'RNA-SEQ' - RNAseq data specific to tissues [see 'self.get_RNA_SEQ' property]  

        Returns:  
            dict (dict) - full enrichment data


<br />

### 2. Single Gene Set Analysis<a id="ans2"></a>

```
from gedspy import Analysis

# initiate class
ans = Analysis(input_data)
```


    The `Analysis` class provides tools for statistical and network analysis of `Enrichment` class results obtained using the `self.get_results` method.
    
        Args:
            input_data (dict) - output data from the `Enrichment` class `self.get_results` method
            
<br />



#### 2.1 Set parameters <a id="sp2"></a>


##### 2.1.1 Interaction parameters <a id="ip2"></a>


```
ans.interactions_metadata
```

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
<br />


```
ans.set_interaction_strength(value)
```

    This method sets self.interaction_strength parameter.
        
        The 'interaction_strength' value is used for enrichment strenght of STRING data:
             *900 - very high probabylity of interaction; 
             *700 - medium probabylity of interaction, 
             *400 - low probabylity of interaction, 
             *<400 - very low probabylity of interaction
             
        Args:
            value (int) - value of interaction strength

<br />


```
ans.set_interaction_source(sources_list)
```

    This method sets self.interaction_source parameter.
        
        The 'interaction_source' value is list of sources for interaction estimation:
            
            *STRING / IntAct: ['STRING', 'Affinomics', 'Alzheimers','BioCreative', 
                                'Cancer', 'Cardiac', 'Chromatin', 'Coronavirus', 
                                'Diabetes', "Huntington's", 'IBD', 'Neurodegeneration', 
                                'Parkinsons']
            
        Args:
            sources_list (list) - list of source data for interactions network analysis

<br />


##### 2.1.2 Network parameters <a id="np2"></a>



```
ans.networks_metadata
```

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


<br />


```
ans.set_p_value(value)
```

    This method sets the p-value threshold for network creation
            
        Args:
            value (float) - p-value threshold for network creation


<br />



```
ans.set_test(test)
```

    This method sets the statistical test to be used for network creation.

            Avaiable tests:
                - 'FISH' - Fisher's exact test
                - 'BIN' - Binomial test
                    
            Args:
                test (str) - test acronym ['FISH'/'BIN']


<br />



```
ans.set_correction(correction)
```

    This method sets the statistical test correction to be used for network creation.

        Avaiable tests:
            - 'BF' - Bonferroni correction
            - 'BH' - Benjamini-Hochberg correction
            - None - lack of correction
                
        Args:
            correction (str / None) - test correction acronym ['BF'/'BH'/None]


<br />



##### 2.1.3 GO-TERM gradation parameter <a id="gp2"></a>



```
ans.set_go_grade(grade)
```

     This method sets self.go_grade parameter.
        
     The 'go_grade' value is used for GO-TERM data gradation [1-4].
            
            Args:
                grade (int) - grade level for GO terms analysis. Default: 1


<br />



#### 2.2 Overrepresentation analysis <a id="op2"></a>


##### 2.2.1 GO-TERM overrepresenation analysis <a id="gop2"></a>


```
ans.GO_overrepresentation()
```

    This method conducts an overrepresentation analysis of Gene Ontology (GO-TERM) information.
        
        Returns:
            Updates `self.GO_stat` with overrepresentation statistics for GO-TERM information.
            To retrieve the results, use the `self.get_GO_statistics` method.


<br />

```
GO_results = ans.get_GO_statistics
```

    This method returns the GO-TERM overrepresentation statistics.
        
        Returns:  
            Returns `self.GO_stat` contains GO-TERM overrepresentation statistics obtained using the `self.GO_overrepresentation` method.

<br />


##### 2.2.2 KEGG overrepresentation analysis <a id="kop2"></a>


```
ans.KEGG_overrepresentation()
```

    This method conducts an overrepresentation analysis of Kyoto Encyclopedia of Genes and Genomes (KEGG) information.
        
        Returns:
            Updates `self.KEGG_stat` with overrepresentation statistics for KEGG information.
            To retrieve the results, use the `self.get_KEGG_statistics` method.

<br />

```
KEGG_results = ans.get_KEGG_statistics
```

    This method returns the KEGG overrepresentation statistics.
        
        Returns:  
            Returns `self.KEGG_stat` contains KEGG overrepresentation statistics obtained using the `self.KEGG_overrepresentation` method.


<br />


##### 2.2.3 Reactome overrepresentation analysis <a id="rop2"></a>


```
ans.REACTOME_overrepresentation()
```

    This method conducts an overrepresentation analysis of Reactome information.
        
        Returns:
            Updates `self.REACTOME_stat` with overrepresentation statistics for Reactome information.
            To retrieve the results, use the `self.get_REACTOME_statistics` method.
<br />

```
REACTOME_results = ans.get_REACTOME_statistics
```

    This method returns the Reactome overrepresentation statistics.
        
        Returns:  
            Returns `self.REACTOME_stat` contains Reactome overrepresentation statistics obtained using the `self.REACTOME_overrepresentation` method.
    

<br />



##### 2.2.4 Viral diseases (ViMIC) overrepresentation analysis <a id="vdop2"></a>


```
ans.ViMIC_overrepresentation()
```

    This method conducts an overrepresentation analysis of viral diseases ViMIC information.
        
        Returns:
            Updates `self.ViMIC_stat` with overrepresentation statistics for ViMIC information.
            To retrieve the results, use the `self.get_ViMIC_statistics` method.


<br />


```
ViMIC_results = ans.get_ViMIC_statistics
```
    This method returns the ViMIC overrepresentation statistics.
        
        Returns:  
            Returns `self.ViMIC_stat` contains ViMIC overrepresentation statistics obtained using the `self.ViMIC_overrepresentation` method.
        

<br />


##### 2.2.5 Human Diseases overrepresentation analysis <a id="hdop2"></a>


```
ans.DISEASES_overrepresentation()
```

    This method conducts an overrepresentation analysis of Human Diseases information.
        
        Returns:
            Updates `self.DISEASE_stat` with overrepresentation statistics for Human Diseases information.
            To retrieve the results, use the `self.get_DISEASE_statistics` method.

<br />


```
DISEASES_results = ans.get_DISEASE_statistics
```
    This method returns the Human Diseases overrepresentation statistics.
        
        Returns:  
            Returns `self.DISEASE_stat` contains Human Diseases overrepresentation statistics obtained using the `self.DISEASES_overrepresentation` method.
        

<br />


##### 2.2.6 Specificity (HPA) overrepresentation analysis <a id="sop2"></a>


```
ans.features_specificity()
```

     This method conducts an overrepresentation analysis of tissue specificity on Human Protein Atlas (HPA) information.
        
        Returns:
            Updates `self.specificity_stat` with overrepresentation statistics for specificity information.
            To retrieve the results, use the `self.get_specificity_statistics` method.

<br />


```
specificity_results = ans.get_specificity_statistics
```

  
    This method returns the tissue specificity [Human Protein Atlas (HPA)] overrepresentation statistics.
        
        Returns:  
            Returns `self.specificity_stat` contains specificity overrepresentation statistics obtained using the `self.features_specificity` method.

        

<br />

<br />



#### 2.3 Gene Interactions (GI) analysis <a id="gi2"></a>



```
ans.gene_interaction()
```

    This method conducts an Genes Interaction (GI) analysis of STRING / IntAct information.
        
        Returns:
            Updates `self.features_interactions` with overrepresentation statistics for GI information.
            To retrieve the results, use the `self.get_features_interactions_statistics` method.


<br />

```
GI_results = ans.get_features_interactions_statistics
```

    This method returns the Genes Interactions (GI) data.
        
        Returns:  
            Returns `self.features_interactions` contains GI data obtained using the `self.gene_interaction` method.


<br />

<br />


#### 2.4 Network analysis <a id="ni2"></a>


##### 2.4.1 Reactome network analysis <a id="rna2"></a>


```
ans.REACTOME_network()
```

    This method conducts an network analysis of Reactome data.
        
        Returns:
            Updates `self.REACTOME_net` with Reactome network data.
            To retrieve the results, use the `self.get_REACTOME_network` method.


<br />

```
Reactome_network = ans.get_REACTOME_network
```

    This method returns the Reactome network analysis results.
        
        Returns:  
            Returns `self.REACTOME_net` contains Reactome network analysis results obtained using the `self.REACTOME_network` method.


<br />


##### 2.4.2 KEGG network analysis <a id="kna2"></a>


```
ans.KEGG_network()
```

     This method conducts an network analysis of KEGG data.
        
        Returns:
            Updates `self.KEGG_net` with Reactome network data.
            To retrieve the results, use the `self.get_KEGG_network` method.


<br />

```
KEGG_network = ans.get_KEGG_network
```

    This method returns the KEGG network analysis results.
        
        Returns:  
            Returns `self.KEGG_net` contains KEGG network analysis results obtained using the `self.KEGG_network` method.


<br />


##### 2.4.3 GO-TERM network analysis <a id="gtna2"></a>


```
ans.GO_network()
```

    This method conducts an network analysis of GO-TERM data.
        
        Returns:
            Updates `self.GO_net` with GO-TERM network data.
            To retrieve the results, use the `self.get_GO_network` method.


<br />

```
GO_network = ans.get_GO_network
```

    This method returns the GO-TERM network analysis results.
        
        Returns:  
            Returns `self.GO_net` contains Reactome network analysis results obtained using the `self.GO_network` method.
        
           


<br />

<br />


#### 2.5 Full enrichment data analysis <a id="feda2"></a>



```
ans.full_analysis()
```

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


<br />


```
full_results = ans.get_full_results
```

    This method returns the full analysis dictionary containing on keys: 
            * 'enrichment':
                - 'gene_info' - genome information for the selected gene set [see `self.get_gene_info` property]
                - 'HPA' - Human Protein Atlas (HPA) [see 'self.get_HPA' property]  
                - 'KEGG' - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see 'self.get_KEGG' property]  
                - 'GO-TERM' - GeneOntology (GO-TERM) [see 'self.get_GO_TERM' property]  
                - 'REACTOME' - Reactome [see 'self.get_REACTOME' property]  
                - 'DISEASES' - Human Diseases [see 'self.get_DISEASES' property]  
                - 'ViMIC' - Viral Diseases (ViMIC) [see 'self.get_ViMIC' property]  
                - 'IntAct' - IntAct [see 'self.get_IntAct' property]  
                - 'STRING' - STRING [see 'self.get_STRING' property]  
                - 'CellConnections' - CellConnections (CellPhone / CellTalk) [see 'self.get_CellCon' property]  
                - 'RNA-SEQ' - RNAseq data specific to tissues [see 'self.get_RNA_SEQ' property]  
                
             * 'statistics':
                 - 'specificity' - Human Protein Atlas (HPA) [see 'self.get_specificity_statistics' property]  
                 - 'KEGG' - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see 'self.get_KEGG_statistics' property]  
                 - 'GO-TERM' - GeneOntology (GO-TERM) [see 'self.get_GO_statistics' property]  
                 - 'REACTOME' - Reactome [see 'self.get_REACTOME_statistics' property]  
                 - 'DISEASES' - Human Diseases [see 'self.get_DISEASE_statistics' property]  
                 - 'ViMIC' - Viral Diseases (ViMIC) [see 'self.get_ViMIC_statistics' property]  
                 - 'interactions' - STRING / IntAct [see 'self.get_features_interactions_statistics' property]  
                 
             * 'networks':
                 - 'KEGG' - Kyoto Encyclopedia of Genes and Genomes (KEGG) [see 'self.get_KEGG_network' property]  
                 - 'GO-TERM' - GeneOntology (GO-TERM) [see 'self.get_GO_network' property]  
                 - 'REACTOME' - Reactome [see 'self.get_REACTOME_network' property]  
    
        Returns:  
            dict (dict) - full analysis data
        
           



<br />

<br />

### 3. Single Gene Set Visualisation<a id="sgs3"></a>

```
from gedspy import Visualization

# initiate class
vis = Visualization(input_data)
```


    The `Visualization` class provides tools for statistical and network analysis of `Analysis` class results obtained using the `self.get_full_results` method.
    
        Args:
            input_data (dict) - output data from the `Analysis` class `self.get_full_results` method
        
            
<br />



#### 3.1 Gene type - pie chart <a id="gt3"></a>


```
plot  =  vis.gene_type_plot(
                cmap = 'summer', 
                image_width = 6, 
                image_high = 6, 
                font_size = 15)
```

    This method generates a pie chart visualizing the distribution of gene types based on enrichment data.

        Args:
            cmap (str) - colormap used for the pie chart. Default is 'summer'
            image_width (int) - width of the plot in inches. Default is 6
            image_high (int) - height of the plot in inches. Default is 6
            font_size (int) - font size. Default is 15

        Returns:
            fig (matplotlib.figure.Figure) - figure object containing a pie chart that visualizes the distribution of gene type occurrences as percentages
        
                    
<br />

#### 3.2 GO-TERMS - bar plot <a id="gtb3"></a>


```
plot  =  vis.GO_plot(   
                p_val = 0.05, 
                test = 'FISH', 
                adj = 'BH', 
                n = 10, 
                min_terms = 5,
                selected_parent = [],
                side = 'right', 
                color = 'blue', 
                width = 10, 
                bar_width = 0.5, 
                stat = 'p_val')
```


     This method generates a bar plot for Gene Ontology (GO) term enrichment and statistical analysis.

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
        
                    
<br />

#### 3.3 KEGG - bar plot <a id="kbp3"></a>


```
plot  =  vis.KEGG_plot(   
                p_val = 0.05, 
                test = 'FISH', 
                adj = 'BH', 
                n = 10, 
                min_terms = 5,
                selected_parent = [],
                side = 'right', 
                color = 'orange', 
                width = 10, 
                bar_width = 0.5, 
                stat = 'p_val')
```


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
        
                    
<br />

#### 3.4 Reactome - bar plot <a id="rbp3"></a>


```
plot  =  vis.REACTOME_plot(   
                p_val = 0.05, 
                test = 'FISH', 
                adj = 'BH', 
                n = 10, 
                min_terms = 5,
                selected_parent = [],
                side = 'right', 
                color = 'silver', 
                width = 10, 
                bar_width = 0.5, 
                stat = 'p_val')
```


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
        
                    
<br />

#### 3.5 Specificity - bar plot <a id="sbp3"></a>


```
plot  =  vis.SPECIFICITY_plot(   
                p_val = 0.05, 
                test = 'FISH', 
                adj = 'BH', 
                n = 5, 
                side = 'right', 
                color = 'bisque', 
                width = 10, 
                bar_width = 0.5, 
                stat = 'p_val')
```


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
        
                    
<br />

#### 3.6 Human Diseases - bar plot <a id="hbp3"></a>


```
plot  =  vis.DISEASES_plot(   
                p_val = 0.05, 
                test = 'FISH', 
                adj = 'BH', 
                n = 5, 
                side = 'right', 
                color = 'thistle', 
                width = 10, 
                bar_width = 0.5, 
                stat = 'p_val')
```


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
        
                    
<br />


#### 3.7 Viral Diseases (ViMIC) - bar plot <a id="vbp3"></a>


```
plot  =  vis.ViMIC_plot(   
                p_val = 0.05, 
                test = 'FISH', 
                adj = 'BH', 
                n = 5, 
                side = 'right', 
                color = 'aquamarine', 
                width = 10, 
                bar_width = 0.5, 
                stat = 'p_val')
```


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
        
                    
<br />


#### 3.8 Blood markers - bar plot <a id="bbp3"></a>


```
plot  =  vis.blod_markers_plot(   
                    n = 10, 
                    side = 'right', 
                    color = 'red', 
                    width = 10, 
                    bar_width = 0.5)
```


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
        
                    
<br />


#### 3.9 GOPa - network <a id="gopa3"></a>


```
plot  =  vis.GOPa_network_create( 
                            data_set = 'GO-TERM', 
                            genes_inc = 10, 
                            gene_int = True, 
                            genes_only = True, 
                            min_con = 2, 
                            children_con = False,
                            include_childrend = True,
                            selected_parents = [],
                            selected_genes = [])
```


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
        
                    
<br />

#### 3.10 Genes Interactions (GI) - network <a id="gipa3"></a>


```
plot  =  vis.GI_network_create(min_con = 2)
```


    This method creates a gene or protein interaction network graph.

        Args:
            min_con (int) - minimum number of connections (degree) required for a gene or protein to be included in the network. Default is 2
    
        Returns:
            fig (networkx.Graph) - NetworkX Graph object representing the interaction network, with nodes sized by connection count and edges colored by interaction type
        
        
                    
<br />

#### 3.11 GOPa AutoML - network <a id="aml3"></a>


```
plot  =  vis.AUTO_ML_network( 
                        genes_inc = 10, 
                        gene_int = True, 
                        genes_only = True, 
                        min_con = 2, 
                        children_con = False, 
                        include_childrend = False,
                        selected_parents = [],
                        selected_genes = [])
```


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
        
        
                    
<br />

#### 3.12 RNAseq tissue - scatter plot <a id="rnaset3"></a>


```
plot  =  vis.gene_scatter( 
                     colors = 'viridis', 
                     species = 'human', 
                     hclust = 'complete', 
                     img_width = None, 
                     img_high = None, 
                     label_size = None, 
                     x_lab = 'Genes', 
                     legend_lab = 'log(TPM + 1)',
                     selected_list = [])
```


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
        
        
        
                    
<br />

<br />

### 4. Differential Set Analysis (DSA)<a id="dsa4"></a>

```
from gedspy import DSA

# initiate class
dsa_compare = DSA(set1, set2)
```


    The 'DSA' class performs Differential Set Analysis by taking the results from two independent feature lists (e.g., upregulated and downregulated genes). 
    It utilizes input data derived from independent gene sets obtained through statistical and network analyses, which are part of the Analysis class results. 
    These results are accessed using the 'self.get_full_results' method.


        Args:
            set1 (dict)- output data from the `Analysis` class `self.get_full_results` method of genes set eg. ['KIT', 'EDNRB', 'PAX3'] 
            set2 (dict)- output data from the `Analysis` class `self.get_full_results` method of genes set eg. ['MC4R', 'MITF', 'SLC2A4'] 
        
    
        
            
<br />



#### 4.1 DSA - FC parameter <a id="dsaf4"></a>


```
dsa_compare.set_min_fc(fc)
```

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
        


<br />



#### 4.2 GO-TERM - DSA <a id="godsa4"></a>


```
dsa_compare.GO_diff()
```

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


<br />

```
GO_diff_results = ans.get_GO_diff
```

    This method returns the GO-TERM Differential Set Analysis (DSA)
    
        Returns:  
            Returns `self.GO` contains GO-TERM DSA obtained using the `self.GO_diff` method.

<br />


#### 4.3 KEGG - DSA <a id="kodsa4"></a>


```
dsa_compare.KEGG_diff()
```

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


<br />

```
KEGG_diff_results = ans.get_KEGG_diff
```

    This method returns the KEGG Differential Set Analysis (DSA)
    
        Returns:  
            Returns `self.KEGG contains KEGG DSA obtained using the `self.KEGG_diff` method.

<br />


#### 4.4 Reactome - DSA <a id="rodsa4"></a>


```
dsa_compare.REACTOME_diff()
```

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


<br />

```
Reactome_diff_results = ans.get_REACTOME_diff
```

    This method returns the Reactome Differential Set Analysis (DSA)
    
        Returns:  
            Returns `self.REACTOME` contains Reactome DSA obtained using the `self.REACTOME_diff` method.

<br />


#### 4.5 Specificity (HPA) - DSA <a id="sodsa4"></a>


```
dsa_compare.spec_diff()
```

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


<br />

```
specificity_diff_results = ans.get_specificity_diff
```

    This method returns the specificity (HPA) Differential Set Analysis (DSA)
    
        Returns:  
            Returns `self.specificity` contains specificity DSA obtained using the `self.get_specificity_diff` method.

<br />

#### 4.6 Genes Interactions (GI) - DSA <a id="gdsa4"></a>


```
dsa_compare.gi_diff()
```

    This method performs a Differential Set Analysis (DSA) to compare two sets (set1 and set2) based on their Genes Interactions (GI) enrichment analysis.
        
        Overview:
            This method assesses differences between set1 and set2 by identifying gene/protein interactions that occur between set1 and set2, but were not found independently in either set1 or set2.
        
        Returns:
            Updates `self.GI` with Reactome DSA data.
            To retrieve the results, use the `self.get_GI_diff` method.


<br />

```
GI_diff_results = ans.get_GI_diff
```

    This method returns the Genes Interactions (GI) Differential Set Analysis (DSA)
    
        Returns:  
            Returns `self.GI` contains GO-TERM DSA obtained using the `self.gi_diff` method.

<br />


#### 4.7 Network analysis - DSA <a id="nadsa4"></a>


```
dsa_compare.network_diff()
```

    This method performs a Differential Set Analysis (DSA) to compare two sets (set1 and set2) based on their network of GO-TERM, KEGG, and Reactome network analysis.
        
        Overview:
            This method assesses differences between set1 and set2 by identifying gene/protein occurrences that are enriched in the combined data of set1 and set2, but are not present independently in either set1 or set2.
        
        Returns:
            Updates `self.networks` with network DSA data.
            To retrieve the results, use the `self.get_networks_diff` method.

<br />

```
network_diff_results = ans.get_networks_diff
```

    This method returns the network Differential Set Analysis (DSA)
    
        Returns:  
            Returns `self.networks` contains networks DSA obtained using the `self.get_networks_diff` method.

<br />


#### 4.8 Inter CellConnection (ICC) - DSA <a id="iccdsa4"></a>


```
dsa_compare.connections_diff()
```

    This method selects elements from the GEDS database that are included in the CellPhone/CellTalk (CellConnections) information for two sets of features.  
        
        It allows the identification of ligand-to-receptor connections, including:
            * set1 -> set2
            * set2 -> set1
        
        Returns:  
            Updates `self.lr_con_set1_set2` and `self.lr_con_set2_set1` with CellPhone / CellTalk information.  
            To retrieve the results, use the `self.get_set_to_set_con` method.  

<br />

```
connections_diff_results = dsa_compare.get_set_to_set_con
```

    This method returns the CellTalk/CellPhone (CellConnecctions) Differential Set Analysis (DSA)
    
        Returns:  
            Returns dict {'set1->set2':'self.lr_con_set1_set2', 'set2->set1':'self.lr_con_set2_set1'} contains CellConnecctions DSA obtained using the `self.connections_diff` method.

<br />



#### 4.9 Inter Terms (IT) - DSA <a id="itdsa4"></a>


```
dsa_compare.inter_processes()
```

    This method performs Differential Set Analysis (DSA) to compare two datasets (set1 and set2).  
        It identifies new terms or pathways in the combined set1 and set2 data, enabling enrichment analysis and presenting inter terms for:
            - GO-TERM
            - KEGG
            - Reactome
            - specificity (HPA)
        
        Returns:
            Updates `self.inter_terms` with Inter Terms DSA data.
            To retrieve the results, use the `self.get_inter_terms` method.

<br />

```
IT_results = dsa_compare.get_inter_terms
```

    This method returns the Inter Terms analysis results.
        
        Returns:  
            Returns `self.inter_terms` contains Inter Terms analysis results obtained using the `self.inter_processes` method.

<br />



#### 4.10 Full analysis - DSA <a id="fuldsa4"></a>


```
dsa_compare.full_analysis()
```

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

<br />

```
full_dsa_results = dsa_compare.get_results
```

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

<br />



<br />

### 5. Differential Set Analysis (DSA) Visualisation <a id="dsav5"></a>

```
from gedspy import Visualization

# initiate class
vis_des = VisualizationDES(input_data)
```


    The `Visualization` class provides tools for statistical and network analysis of `Analysis` class results obtained using the `self.get_full_results` method.
    
        Args:
            input_data (dict) - output data from the `Analysis` class `self.get_full_results` method
        
            
<br />


#### 5.1 Both sets graphs <a id="dsav5b"></a>
##### 5.1.1 Gene type - pie chart <a id="gtdsav5"></a>


```
plot  =  vis_des.diff_gene_type_plot( 
                            set1_name = 'Set 1', 
                            set2_name = 'Set 2', 
                            image_width = 12, 
                            image_high = 6, 
                            font_size = 15)
```

    This method generates a pie chart visualizing the distribution of gene types based on set1 and set2 enrichment data.

        Args:
            set1_name (str) - name for the set1 data. Default is 'Set 1', 
            set2_name (str) - name for the set2 data. Default is 'Set 2', 
            image_width (int) - width of the plot in inches. Default is 12
            image_high (int) - height of the plot in inches. Default is 6
            font_size (int) - font size. Default is 15

        Returns:
            fig (matplotlib.figure.Figure) - figure object containing a pie chart that visualizes the distribution of gene type occurrences as percentages
        
                    
<br />

##### 5.1.2 GO-TERMS - bar plot <a id="godsav5"></a>


```
plot  =  vis_des.diff_GO_plot(   
                        p_val = 0.05, 
                        test = 'FISH', 
                        adj = 'BH', 
                        n = 25, 
                        min_terms = 5,
                        selected_parent = [],
                        width = 10, 
                        bar_width = 0.5, 
                        stat = 'p_val')
```


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
        
                    
<br />

##### 5.1.3 KEGG - bar plot <a id="kdsav5"></a>


```
plot  =  vis_des.diff_KEGG_plot(   
                        p_val = 0.05, 
                        test = 'FISH', 
                        adj = 'BH', 
                        n = 25, 
                        min_terms = 5,
                        selected_parent = [],
                        width = 10, 
                        bar_width = 0.5, 
                        stat = 'p_val')
```


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
        
                    
<br />

##### 5.1.4 Reactome - bar plot <a id="rdsav5"></a>


```
plot  =  vis_des.diff_REACTOME_plot(   
                        p_val = 0.05, 
                        test = 'FISH', 
                        adj = 'BH', 
                        n = 25, 
                        min_terms = 5,
                        selected_parent = [],
                        width = 10, 
                        bar_width = 0.5, 
                        stat = 'p_val')
```


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
        
                    
<br />

##### 5.1.5 Specificity - bar plot <a id="sdsav5"></a>


```
plot  =  vis_des.diff_SPECIFICITY_plot(   
                        p_val = 0.05, 
                        test = 'FISH', 
                        adj = 'BH', 
                        n = 5, 
                        min_terms = 1,
                        selected_set = [],
                        width = 10, 
                        bar_width = 0.5, 
                        stat = 'p_val')
```


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
        
                    
<br />

##### 5.1.6 Human Diseases - bar plot <a id="hdsav5"></a>


```
plot  =  vis.DISEASES_plot(   
                p_val = 0.05, 
                test = 'FISH', 
                adj = 'BH', 
                n = 5, 
                side = 'right', 
                color = 'thistle', 
                width = 10, 
                bar_width = 0.5, 
                stat = 'p_val')
```


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
        
                    
<br />


##### 5.1.7 Viral Diseases (ViMIC) - bar plot <a id="vdsav5"></a>


```
plot  =  vis.ViMIC_plot(   
                p_val = 0.05, 
                test = 'FISH', 
                adj = 'BH', 
                n = 5, 
                side = 'right', 
                color = 'aquamarine', 
                width = 10, 
                bar_width = 0.5, 
                stat = 'p_val')
```


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
        
                    
<br />



##### 5.1.8 GOPa - network <a id="gopasav5"></a>


```
plot  =  vis.GOPa_network_create( 
                            data_set = 'GO-TERM', 
                            genes_inc = 10, 
                            gene_int = True, 
                            genes_only = True, 
                            min_con = 2, 
                            children_con = False,
                            include_childrend = True,
                            selected_parents = [],
                            selected_genes = [])
```


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
        
                    
<br />

##### 5.1.9 Genes Interactions (GI) - network <a id="gisav5"></a>


```
plot  =  vis.GI_network_create(min_con = 2)
```


    This method creates a gene or protein interaction network graph.

        Args:
            min_con (int) - minimum number of connections (degree) required for a gene or protein to be included in the network. Default is 2
    
        Returns:
            fig (networkx.Graph) - NetworkX Graph object representing the interaction network, with nodes sized by connection count and edges colored by interaction type
        
        
                    
<br />

##### 5.1.10 GOPa AutoML - network <a id="gopaml5"></a>


```
plot  =  vis.AUTO_ML_network( 
                        genes_inc = 10, 
                        gene_int = True, 
                        genes_only = True, 
                        min_con = 2, 
                        children_con = False, 
                        include_childrend = False,
                        selected_parents = [],
                        selected_genes = [])
```


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
        
        
                    
<br />

##### 5.1.11 RNAseq tissue - scatter plot <a id="rnaseq5"></a>


```
plot  =  vis.gene_scatter( 
                     colors = 'viridis', 
                     species = 'human', 
                     hclust = 'complete', 
                     img_width = None, 
                     img_high = None, 
                     label_size = None, 
                     x_lab = 'Genes', 
                     legend_lab = 'log(TPM + 1)',
                     selected_list = [])
```


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
        
        
        
                    
<br />




##### 5.1.12 Adjusted Terms - Heatmap <a id="rnaseq6"></a>

This module allows manual adjustment of enrichment or over-representation results and visualizes differences between term sets using a heatmap.

##### Features
- Manual curation of enrichment / over-representation terms  
- Comparison of multiple datasets or conditions  
- Visualization of similarities and differences between term sets  
- Clear and interpretable heatmap output  

##### Example Workflow
1. Load enrichment or over-representation results  
2. Manually adjust selected terms  
3. Generate a heatmap to compare adjusted term sets across datasets  

##### Input
- Enrichment / over-representation analysis results (e.g. GO, KEGG, Reactome)

##### Output
- Heatmap displaying adjusted terms across datasets


<br />


```
figure = enrichment_heatmap(data = data, 
                       stat_col = stat_col, 
                       term_col = term_col,
                       set_col = set_col,
                       sets = sets,
                       title = title,
                       fig_size = fig_size,
                       font_size = 16,
                       scale = True) 
```


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
        
        
        
                    
<br />



<br />

### 6. GetData<a id="gd6"></a>

The data sets are annotated to the Ref_Genome (get_REF_GEN()) by ids

```
from gedspy import GetData

# initiate class
gd = GetData()
```



#### 6.1 Get combined genome <a id="gdcg6"></a>

*  Homo sapiens / Mus musculus / Rattus norvegicus

```
ref_gen = gd.get_REF_GEN()
```

    This method gets the REF_GEN which is the combination of Homo sapiens / Mus musculus / Rattus norvegicus genomes for scientific use.
        
        Returns:
            dict: Combination of Homo sapiens / Mus musculus / Rattus norvegicus genomes      

<br />


#### 6.2 Get annotated RNAseq data <a id="gard6"></a>

*  Homo sapiens

```
ref_gen_seq = gd.get_REF_GEN_RNA_SEQ()
```

    This method gets the tissue-specific RNA-SEQ data including:
        -human_tissue_expression_HPA
        -human_tissue_expression_RNA_total_tissue
        -human_tissue_expression_fetal_development_circular

    
    Returns:
        dict: Tissue specific RNA-SEQ data

<br />

#### 6.3 Get annotated Reactome data <a id="gare6"></a>


```
reactome = gd.get_REACTOME()
```

    This method gets the REACTOME data including the id to connect with REF_GENE by id_reactome
    
        Returns:
           dict: REACTOME data
                

<br />


#### 6.4 Get annotated HPA data <a id="ghpa6"></a>


```
HPA = gd.get_HPA()
```

    This method gets the HPA (Human Protein Atlas) data including the id to connect with REF_GENE by id_HPA
            
        Returns:
            dict: HPA data

<br />

#### 6.5 Get annotated Human Diseases data <a id="gahd6"></a>


```
disease = gd.get_DISEASES()
```

    This method gets the DISEASES data including the id to connect with REF_GENE by id_diseases

        Returns:
            dict: DISEASES data

<br />

#### 6.6 Get annotated viral diseases (ViMIC) data <a id="gavm6"></a>


```
vimic = gd.get_ViMIC()
```

    This method gets the ViMIC data including the id to connect with REF_GENE by id_viral_diseases
         
        Returns:
           dict: ViMIC data

<br />

#### 6.7 Get annotated KEGG data <a id="gkeg6"></a>


```
kegg = gd.get_KEGG()
```

    This method gets the KEGG data including the id to connect with REF_GENE by id_KEGG

        Returns:
           dict: KEGG data

<br />

#### 6.8 Get annotated GO-TERM data <a id="gago6"></a>


```
go = gd.get_GO()
```

    This method gets the GO-TERM data including the id to connect with REF_GENE by id_GO
         
        Returns:
           dict: GO-TERM data

<br />

#### 6.9 Get annotated IntAct data <a id="gaia6"></a>


```
intact = gd.get_IntAct()
```

    This method gets the IntAct data including the id to connect with REF_GENE by id_IntAct

        Returns:
           dict: IntAct data

<br />

#### 6.10 Get annotated STRING data <a id="gast6"></a>


```
string = gd.get_STRING()
```

    This method gets the STRING data including the id to connect with REF_GENE by id_string
         
        Returns:
           dict: STRING data

<br />


#### 6.11 Get adjusted CellTalk data <a id="gact6"></a>


```
cell_talk = gd.get_CellTalk()
```

    This method gets the CellTalk data.
    
    Source: https://tcm.zju.edu.cn/celltalkdb/

         
        Returns:
           dict: CellTalk data

<br />

#### 6.12 Get adjusted CellPhone data <a id="gacp6"></a>


```
cell_phone = gd.get_CellPhone()
```

    This method gets the CellPhone data after adjustment.
         
        Returns:
           dict: CellPhone data

<br />

#### 6.13 Get annotated CellInteraction data <a id="gaci6"></a>


```
cell_interactions = gd.get_interactions()
```

    This method gets the CellPhone & CellTalk data including the id to connect with REF_GENE by id_cell_int.
         
        Returns:
           dict: CellInteractions data

<br />




<br />

### 7. GetRawData<a id="grd7"></a>

```
from gedspy import GetRawData

# initiate class
gdr = GetDataRaw()
```



#### 7.1 Get combined genome <a id="gdcg7"></a>

*  Homo sapiens / Mus musculus / Rattus norvegicus

```
ref_gen = gdr.get_raw_REF_GEN()
```

    This method gets the REF_GEN which is the combination of Homo sapiens / Mus musculus / Rattus norvegicus genomes for scientific use.
            
    Source: NCBI [https://www.ncbi.nlm.nih.gov/]

        Returns:
            dict: Combination of Homo sapiens / Mus musculus / Rattus norvegicus genomes
                    

<br />


#### 7.2 Get RNAseq data <a id="gard7"></a>

*  Homo sapiens

```
ref_gen_seq = gdr.get_raw_REF_GEN_RNA_SEQ()
```

    This method gets the tissue-specific RNA-SEQ data including:
        -human_tissue_expression_HPA
        -human_tissue_expression_RNA_total_tissue
        -human_tissue_expression_fetal_development_circular

    Source: NCBI [https://www.ncbi.nlm.nih.gov/]

      
        Returns:
           dict: Tissue specific RNA-SEQ data
<br />

#### 7.3 Get raw Reactome data <a id="gare7"></a>


```
recteome = gdr.get_raw_REACTOME()
```

    This method gets the REACTOME data downloaded from source.
    
    Source: https://reactome.org/
    
        Returns:
           dict: REACTOME data
                

<br />


#### 7.4 Get raw HPA data <a id="ghpa7"></a>


```
HPA = gdr.get_raw_HPA()
```

    This method gets the HPA (Human Protein Atlas) data.
    
    Source: https://www.proteinatlas.org/

         
        Returns:
           dict: HPA data

<br />

#### 7.5 Get raw Human Diseases data <a id="gahd7"></a>


```
diseases = gdr.get_raw_DISEASES()
```

    This method gets the Human Diseases data.
        
    Source: https://diseases.jensenlab.org/Search


        Returns:
           dict: DISEASES data

<br />

#### 7.6 Get raw viral diseases (ViMIC) data <a id="gavm7"></a>


```
vimic = gdr.get_raw_ViMIC()
```

    This method gets the ViMIC data.
        
    Source: http://bmtongji.cn/ViMIC/index.php

         
        Returns:
           dict: ViMIC data

<br />

#### 7.7 Get raw KEGG data <a id="gkeg7"></a>


```
kegg = gdr.get_raw_KEGG()
```

    This method gets the KEGG data.
        
    Source: https://www.genome.jp/kegg/


        Returns:
           dict: KEGG data

<br />

#### 7.8 Get raw GO-TERM data <a id="gago7"></a>


```
go = gdr.get_raw_GO()
```

    This method gets the GO-TERM data.
        
    Source: https://geneontology.org/

         
        Returns:
           dict: GO-TERM data

<br />

#### 7.9 Get raw IntAct data <a id="gaia7"></a>


```
intact = gdr.get_raw_IntAct()
```

    This method gets the IntAct data.
    
    Source: https://www.ebi.ac.uk/intact/home


        Returns:
           dict: IntAct data

<br />

#### 7.10 Get raw STRING data <a id="gast7"></a>


```
string = gdr.get_raw_STRING()
```

    This method gets the STRING data.
    
    Source: https://string-db.org/

         
        Returns:
           dict: STRING data

<br />


#### 7.11 Get raw CellTalk data <a id="gact7"></a>


```
cell_talk = gdr.get_raw_CellTalk()
```

    This method gets the CellTalk data.
    
    Source: https://tcm.zju.edu.cn/celltalkdb/

         
        Returns:
           dict: CellTalk data

<br />

#### 7.12 Get raw CellPhone data <a id="gacp7"></a>


```
cell_phone = gdr.get_raw_CellPhone()
```

    This method gets the CellPhone data.
        
    Source: https://www.cellphonedb.org/

         
        Returns:
           dict: CellPhone data

<br />




<br />

### 8. DataDownloading<a id="grd8"></a>

```
from gedspy import DataDownloading

# initiate class
dw = Donwload()
```

#### 8.1 Reference genome <a id="gdcg8"></a>


```
ref = dw.download_ref()
```

	This method downloads and returns combined human/rat/mice reference genome.
    
	Source: NCBI [https://www.ncbi.nlm.nih.gov/]
        
        Returns:
            dict (dict) - ref_genome
                

<br />

#### 8.2 RNAseq data <a id="gard8"></a>


```
rnaseq = dw.download_rns_seq()
```

    This method downloads and returns the tissue-specific RNA-SEQ data including:
        -human_tissue_expression_HPA
        -human_tissue_expression_RNA_total_tissue
        -human_tissue_expression_fetal_development_circular

	Source: NCBI [https://www.ncbi.nlm.nih.gov/]
        
        Returns:
            dict (dict) - RNAseq data
                

<br />

#### 8.3 IntAct data <a id="gare8"></a>


```
IntAct = dw.download_IntAct_data()
```

	This method downloads and returns IntAct data.
	
	Source: https://www.ebi.ac.uk/intact/home
    
        Returns:
            dict (dict) - IntAct data
                

<br />

#### 8.4 Human diseases data <a id="ghpa8"></a>


```
diseases = dw.download_diseases()
```

    This method downloads and returns Diseases data.

    Source: https://diseases.jensenlab.org/

    
        Returns:
            dict (dict) - diseases data
                

<br />


#### 8.5 Viral diseases data <a id="gahd8"></a>


```
ViMIC = dw.download_viral_deiseases()
```

	This method downloads and returns ViMIC (viruses) data.

	Source: http://bmtongji.cn/ViMIC/index.php

    
        Returns:
            dict (dict) - viruses (ViMIC) data
                

<br />


#### 8.6 Human Protein Atlas - tissue / cell data <a id="gavm8"></a>


```
HPA = dw.download_HPA()
```

	This method downloads and returns Human Protein Atlas (HPA) tissue/cell data.
	
	Source: https://www.proteinatlas.org/
	
      
        Returns:
            dict (dict) - HPA data
                

<br />


#### 8.7 STRING - interaction data <a id="gkeg8"></a>


```
string = dw.download_string()
```

	This method downloads and returns STRING human/mouse/rat interaction data.

	Source: https://string-db.org/
        
      
        Returns:
            dict (dict) - STRING data
                

<br />


#### 8.8 KEGG data <a id="gago8"></a>


```
kegg = dw.download_kegg()
```

	This method downloads and returns KEGG data.
	
	Source: https://www.genome.jp/kegg/
	
      
        Returns:
            dict (dict) - KEGG data
                

<br />

#### 8.9 REACTOME data <a id="gaia8"></a>


```
reactome = dw.download_reactome()
```

  	This method downloads and returns REACTOME data.
      
    Source: https://reactome.org/
        
      
        Returns:
            dict (dict) - REACTOME data
                

<br />

#### 8.10 GO-TERM data <a id="gast8"></a>


```
go = dw.download_go_term()
```

  	This method downloads and returns GO-TERM data.
      
    Source: https://geneontology.org/
        
      
        Returns:
            dict (dict) - GO-TERM data
                

<br />

#### 8.11 CellTalk data <a id="gact8"></a>


```
cell_talk = dw.download_cell_talk()
```

  	This method downloads and returns CellTalk data.
      
    Source: https://tcm.zju.edu.cn/celltalkdb/
        
      
        Returns:
            dict (dict) - CellTalk data
                

<br />

#### 8.12 CellPhone data <a id="gacp8"></a>


```
cell_phone = dw.download_cell_phone()
```

	This method downloads and returns CellPhone data.
	
	Source: https://www.cellphonedb.org/
        
      
        Returns:
            dict (dict) - CellPhone data
                

<br />

<br />

### 9. UpdatePanel<a id="up9"></a>

```
from gedspy import UpdatePanel

# initiate class
up = UpdatePanel()
```

#### 9.1 Check last update of data <a id="chlu9"></a>


```
up.check_last_update()
```

	This method checks the last update of GEDS data used in this library
           
        Returns:
           date: Date of last update
                

<br />

#### 9.2 Update data from GEDSdb <a id="udfg9"></a>


```
up.update_library_database()
```

	This method checks if the newest version of GEDS data is available for the GEDSpy library and updates it.
       
        Args:
            force (bool) - if True user force update of GEDS data independent of the GEDSpy version
            URL (str) - provide URL of the database you wish to use. Default: URL for the newest db version
           
        Returns:
            Updated by the author the newest version of GEDS data base.
                

<br />

#### 9.3 Update data from data sources <a id="udfs9"></a>


```
up.update_from_sources()
```

	This method checks if the newest version of GEDS data is available for the GEDSpy library and updates it.
       
        Args:
            force (bool) - if True user force update of GEDS data independent of the GEDSpy version
           
        Returns:
            Updated by the author the newest version of GEDS data base.
                

<br />

<br />


### 10. Example enrichment analysis of single set <a id="ex10"></a>


<br />

```
# Example analysis gene list   

gene_list = ['CACNA1I','CALD1','CAMK1G','CAMK2N1','CAMSAP1','CCL15','CCL16','CCNL2','CCT8P1','CD46','CDC14A','CDK18','CDK19','CES3','CHEK2',
			 'CHID1','COL6A3','CPVL','CYP3A43','CYP3A5','DBNL','DUSP10','DUSP9','ECHS1','EGFR','EGR2','ELL2','ERMP1','ESR1','F7','FAM171A1',
			 'FAM20C','FGFR2','FH','FLAD1','FUT3','GAA','GBA2','GGCX','GJB1','GLRX5','GNAI2','GNB2','GNB3','GPNMB','GRB10','GRHPR','HMGCS2',
			 'HSD17B4','HSP90AB1','IER3IP1','IGF2R','IL1R1','INF2','IRAK1','ITGA1','ITGA7','ITIH1','ITIH3','ITIH4','ITPR1','ITSN1','JAK1',
			 'KALRN','KCNQ2','KCNQ4','KDM3A','KMO','KRAS','KSR1','LAMA5','LAMB2','LCN2','MAP2K7','MAP4K2','MAP4K3',
			 'MAPK13','MARCO','MAST2','MAT1A','MATR3','MCM8','MFSD10','MGAT5','MTMR10','MUSK','MYO9B','NBAS']

    
    
from gedspy import Enrichment

# create instance of the Enrichment class
enr = Enrichment()


# select featrues from genes/proteins list for Homo sapiens / Mus musculus / Rattus norvegicus
enr.select_features(gene_list)
```

<br />

```
# get selected genes/proteins info
gene_info = enr.get_gene_info
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/gene_info.bmp" alt="drawing" width="700" />
</p>


<br />

```
# There are two way of enrich data:
# * each data separately:
    
# Human protein Atlas data
enr.enriche_specificiti()

HPA = enr.get_HPA
```


<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/hpa.bmp" alt="drawing" width="700" />
</p>

<br />


```
# KEGG data
enr.enriche_KEGG()

KEGG = enr.get_KEGG
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/kegg.bmp" alt="drawing" width="700" />
</p>

<br />


```
# GO-TERM data
enr.enriche_GOTERM()

GOTERM = enr.get_GO_TERM
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/goterm.bmp" alt="drawing" width="700" />
</p>

<br />


```
# Reactome data
enr.enriche_REACTOME()

REACTOME = enr.get_REACTOME
```


<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/reactome.bmp" alt="drawing" width="700" />
</p>

<br />


```
# Human Diseases data
enr.enriche_DISEASES()

DISEASES = enr.get_DISEASES
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/diseases.bmp" alt="drawing" width="700" />
</p>

<br />


```
# ViMic data
enr.enriche_ViMIC()

ViMIC = enr.get_ViMIC
```


<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/vimic.bmp" alt="drawing" width="700" />
</p>

<br />


```
# IntAct data
enr.enriche_IntAct()

IntAct = enr.get_IntAct
```


<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/intact.bmp" alt="drawing" width="700" />
</p>

<br />


```
# STRING data
enr.enriche_STRING()

STRING = enr.get_STRING
```


<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/string.bmp" alt="drawing" width="600" />
</p>

<br />


```
# CellCon data
enr.enriche_CellCon()

CellConnections = enr.get_CellCon
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/cellcon.bmp" alt="drawing" width="700" />
</p>

<br />


```
# RNAseq data
enr.enriche_RNA_SEQ()

RNASEQ = enr.get_RNA_SEQ   
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/rnaseq.bmp" alt="drawing" width="700" />
</p>

<br />

```
# * all data in parallel:


enr.full_enrichment()


# get_results can be used for return all data enriched separately like above ^^^
results = enr.get_results
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/enr/fullenr.bmp" alt="drawing" width="700" />
</p>

<br />


```
# import the Analysis class from the Enrichment module
from gedspy import Analysis

# create instance of the Analysis class with results from get_results
ans = Analysis(results)

# adjustment of analysis parameters
# for more details go to documentation on GitHub

# network parameters
ans.networks_metadata

# interactions parameters
ans.interactions_metadata

# set analysis parameter (default parameters check in documentation on GitHub)
ans.set_p_value(value = 0.05)
ans.set_test(test = 'FISH')       
ans.set_correction(correction = None)    
 
ans.networks_metadata
```

<br />


```
# Overrepresentation analysis
# There are two way of enrich data:
# * each data separately:

# GO-TERM
ans.GO_overrepresentation()

go = ans.get_GO_statistics
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/ovr/goterm.bmp" alt="drawing" width="700" />
</p>

<br />


```
# KEGG
ans.KEGG_overrepresentation()

kegg = ans.get_KEGG_statistics
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/ovr/kegg.bmp" alt="drawing" width="700" />
</p>


<br />


```
# Reactome
ans.REACTOME_overrepresentation()

reactome = ans.get_REACTOME_statistics
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/ovr/reactome.bmp" alt="drawing" width="700" />
</p>


<br />


```
# ViMic
ans.ViMIC_overrepresentation()

vimic = ans.get_ViMIC_statistics
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/ovr/vimic.bmp" alt="drawing" width="700" />
</p>


<br />


```
# Human diseases
ans.DISEASES_overrepresentation()

diseases = ans.get_DISEASE_statistics
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/ovr/humandiseases.bmp" alt="drawing" width="700" />
</p>


<br />


```
# Specificity (HPA)
ans.features_specificity()

spec = ans.get_specificity_statistics
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/ovr/hpa.bmp" alt="drawing" width="700" />
</p>


<br />



```
# Interactions (STRING/IntAct)
ans.gene_interaction()

inter = ans.get_features_interactions_statistics
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/ovr/inter.bmp" alt="drawing" width="600" />
</p>


<br />


```
# Reactome paths network
ans.REACTOME_network()

reactome_net = ans.get_REACTOME_network
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/ovr/reactomenx.bmp" alt="drawing" width="600" />
</p>


<br />


```
# KEGG paths network
ans.KEGG_network()

kegg_net = ans.get_KEGG_network
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/ovr/keggnet.bmp" alt="drawing" width="600" />
</p>


<br />


```
# GO-TERM terms network
ans.GO_network()

go_net = ans.get_GO_network
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/ovr/gonet.bmp" alt="drawing" width="600" />
</p>


<br />


```
# * all data in parallel:


ans.full_analysis()


# get_results can be used for return all data enriched separately like above ^^^
results2 = ans.get_full_results
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/ovr/full.bmp" alt="drawing" width="800" />
</p>


<br />

```
# import the Visualization class from the Enrichment module
from gedspy import Visualization

# load library JVG - display and adjustment Networks and Bar plots
from JVG import JVG

# create instance of the Visualization class with results from get_full_results
vis = Visualization(results2)
```


<br />


```
# gene type
plot  =  vis.gene_type_plot(cmap = 'summer', image_width = 6, image_high = 6, font_size = 15)

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/gtype.bmp" alt="drawing" width="400" />
</p>


<br />


```
# GO-TERM
plot  =  vis.GO_plot(p_val = 0.05, 
                    test = 'FISH', 
                    adj = None, 
                    n = 20, 
                    side = 'left', 
                    color = 'blue', 
                    width = 10, 
                    bar_width = 0.5, 
                    stat = 'p_val')

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/go-term.bmp" alt="drawing" width="650" />
</p>


<br />

```
# Specificity (HPA)
plot  =  vis.SPECIFICITY_plot(p_val = 0.05, 
                    test = 'FISH', 
                    adj = None, 
                    n = 25, 
                    side = 'right', 
                    color = 'bisque', 
                    width = 10, 
                    bar_width = 0.5, 
                    stat = 'p_val')

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/spec.bmp" alt="drawing" width="650" />
</p>


<br />

```
# KEGG
plot  =  vis.KEGG_plot(p_val = 0.05, 
                    test = 'FISH', 
                    adj = None, 
                    n = 25, 
                    side = 'right', 
                    color = 'orange', 
                    width = 10, 
                    bar_width = 0.5, 
                    stat = 'p_val')

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/kegg.bmp" alt="drawing" width="700" />
</p>


<br />

```
# Reactome
plot  =  vis.REACTOME_plot(p_val = 0.05, 
                    test = 'FISH', 
                    adj = None, 
                    n = 25, 
                    side = 'right', 
                    color = 'silver', 
                    width = 10, 
                    bar_width = 0.5, 
                    stat = 'p_val')

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/reactome.bmp" alt="drawing" width="700" />
</p>


<br />

```
# Human diseases
plot  =  vis.DISEASES_plot(p_val = 0.05, 
                    test = 'FISH', 
                    adj = None, 
                    n = 25, 
                    side = 'right', 
                    color = 'thistle', 
                    width = 10, 
                    bar_width = 0.5, 
                    stat = 'p_val')

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/human_diseases.bmp" alt="drawing" width="600" />
</p>


<br />

```
# ViMic
plot  =  vis.ViMIC_plot(p_val = 0.05, 
                    test = 'FISH', 
                    adj = None, 
                    n = 25, 
                    side = 'right', 
                    color = 'aquamarine', 
                    width = 10, 
                    bar_width = 0.5, 
                    stat = 'p_val')

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/vimic.bmp" alt="drawing" width="500" />
</p>


<br />

```
# blood markers
plot  =  vis.blod_markers_plot()

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/blood.bmp" alt="drawing" width="550" />
</p>


<br />

```
# GO-TERM network
go = vis.GOPa_network_create(
                        data_set = 'GO-TERM', 
                        genes_inc = 10, 
                        gene_int = True, 
                        genes_only = True, 
                        min_con = 2, 
                        children_con = True,
                        include_childrend = True,
                        selected_parents = [],
                        selected_genes = [])

nt = JVG.NxEditor(go)
nt.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/gonet.bmp" alt="drawing" width="700" />
</p>


<br />

```
# KEGG network
kegg = vis.GOPa_network_create(
                        data_set = 'KEGG', 
                        genes_inc = 10, 
                        gene_int = True, 
                        genes_only = True, 
                        min_con = 2, 
                        children_con = True,
                        include_childrend = True,
                        selected_parents = ['Nervous system', 'Cell motility'],
                        selected_genes = [])

nt = JVG.NxEditor(kegg)
nt.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/keggnet.bmp" alt="drawing" width="500" />
</p>


<br />

```
# Reactome network
react = vis.GOPa_network_create(
                        data_set = 'REACTOME', 
                        genes_inc = 10, 
                        gene_int = True, 
                        genes_only = True, 
                        min_con = 2, 
                        children_con = False,
                        include_childrend = False,
                        selected_parents = [],
                        selected_genes = ['F7', 'LAMA5'])

nt = JVG.NxEditor(react)
nt.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/reactnet.bmp" alt="drawing" width="450" />
</p>


<br />

```
# Gene interactions network
inter = vis.GI_network_create()

nt = JVG.NxEditor(inter)
nt.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/gi.bmp" alt="drawing" width="700" />
</p>


<br />

```
# AUTO-ML
ml = vis.AUTO_ML_network( 
                    genes_inc = 10, 
                    gene_int = True, 
                    genes_only = True, 
                    min_con = 1, 
                    children_con = True, 
                    include_childrend = True,
                    selected_parents = ['Cell motility', 'Development and regeneration'],
                    selected_genes = ['JAK1', 'KRAS'])

nt = JVG.NxEditor(ml)
nt.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/automl.bmp" alt="drawing" width="600" />
</p>


<br />

```
# RNAseq
seq = vis.gene_scatter( 
                 colors = 'viridis', 
                 species = 'human', 
                 hclust = 'complete', 
                 img_width = None, 
                 img_high = None, 
                 label_size = None, 
                 x_lab = 'Genes', 
                 legend_lab = 'log(TPM + 1)')
```


<br />

```
graph1 = JVG.MplEditor(seq['tissue_expression_HPA'])
graph1.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/hpa.bmp" alt="drawing" width="800" />
</p>


<br />

```
graph2 = JVG.MplEditor(seq['tissue_expression_RNA_total_tissue'])
graph2.edit()

```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/RNAtotal.bmp" alt="drawing" width="800" />
</p>


<br />

```
graph3 = JVG.MplEditor(seq['tissue_expression_fetal_development_circular'])
graph3.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_1/vis/circular.bmp" alt="drawing" width="800" />
</p>


<br />

[Example 1 - file](examples/example_1.py)

<br />

<br />



### 11. Example enrichment analysis of double sets <a id="ex11"></a>


<br />

```
# Example analysis gene lists

gene_list = ['CACNA1I','CALD1','CAMK1G','CAMK2N1','CAMSAP1','CCL15','CCL16','CCNL2','CCT8P1','CD46','CDC14A','CDK18','CDK19','CES3','CHEK2',
			 'CHID1','COL6A3','CPVL','CYP3A43','CYP3A5','DBNL','DUSP10','DUSP9','ECHS1','EGFR','EGR2','ELL2','ERMP1','ESR1','F7','FAM171A1',
			 'FAM20C','FGFR2','FH','FLAD1','FUT3','GAA','GBA2','GGCX','GJB1','GLRX5','GNAI2','GNB2','GNB3','GPNMB','GRB10','GRHPR','HMGCS2',
			 'HSD17B4','HSP90AB1','IER3IP1','IGF2R','IL1R1','INF2','IRAK1','ITGA1','ITGA7','ITIH1','ITIH3','ITIH4','ITPR1','ITSN1','JAK1',
			 'KALRN','KCNQ2','KCNQ4','KDM3A','KMO','KRAS','KSR1','LAMA5','LAMB2','LCN2','MAP2K7','MAP4K2','MAP4K3',
			 'MAPK13','MARCO','MAST2','MAT1A','MATR3','MCM8','MFSD10','MGAT5','MTMR10','MUSK','MYO9B','NBAS']

gene_list2 = ['NCOA6','NCSTN','NDUFA4','NEK4', 'UDT2','NUP210','ORC3L','PAOX','PEMT','PEX14','PFKL','PHKA2','PIM1','PLXND1','PMM1','PON3','POR','PPARG','PPARGC1B',
              'PRKCE','PTK2B','PTP4A1','PTPN23','PTPRF','PTPRK','RARA','RNF10','RNF14','RNF165','ROCK2','RRBP1','RREB1','SCN1A','SDC1','SERPINA1','SERPINA10','SFXN5',
              'SHROOM1','SIL1','SIRPA','SLC12A7','SLC13A3','SLC16A2','SLC17A7','SLC22A23','SLC22A9','SLC25A11','SLC25A25','SLC38A3','SLC45A3','SLC4A5','SLC5A1','SLC7A2',
              'SLC8A3','SLC9A6','SLCO1A2','SLCO1B3','SMARCA2','NX4','SORBS1','SPEN','SPR','SRF','STAB1','STAT1','SUCLG2','SULT1B1','SULT1E1','TBC1D2B','TCHP','TGFBI',
              'TGOLN2','THPO', 'IMM13','TLK2','TMEM62','TNFSF14','TNK2','TNS1','TPI1','TRIB3','TRMT11','TTYH3']


# import the Enrichment & Analysis classes from the Enrichment module
from gedspy import Enrichment
from gedspy import Analysis 
```


<br />

```
#SET1

# create instance of the Enrichment class
enr = Enrichment()

# select featrues from genes/proteins list for Homo sapiens / Mus musculus / Rattus norvegicus for first gene_list
enr.select_features(gene_list)

# conduct full enrichment
enr.full_enrichment()

# get results for first set
results1 = enr.get_results

    
# create instance of the Analysis class
ans = Analysis(results1)

# set parameters or leave default - see manual on GitHub
ans.set_p_value(value = 0.05)
ans.set_test(test = 'FISH')       
ans.set_correction(correction = None)    

# ! parameters for both analyses (set1 and set2) must be the same ! 
 
# conduct full analyses
ans.full_analysis()

# get full results for first set
results1 = ans.get_full_results
```




<br />

```
# create instance of the Enrichment class
enr = Enrichment()

# select featrues from genes/proteins list for Homo sapiens / Mus musculus / Rattus norvegicus for second gene_list
enr.select_features(gene_list2)

# conduct full enrichment
enr.full_enrichment()

# get results for second set
results2 = enr.get_results


# create instance of the Analysis class
ans = Analysis(results2)


# set parameters or leave default - see manual on GitHub
ans.set_p_value(value = 0.05)
ans.set_test(test = 'FISH')       
ans.set_correction(correction = None)    
 
# ! parameters for both analyses (set1 and set2) must be the same ! 
 
# conduct full analyses
ans.full_analysis()

# get full results for second set
results2 = ans.get_full_results
```





<br />

```
# import the DSA class from the Enrichment module
from gedspy import DSA

# create instance of the DSA class with results from get_full_results for set1 and set2
dsa_compare = DSA(results1, results2)
```



<br />

```
# DSA analysis
# There are two way of enrich data:
# * each data separately:
     
# GO-TERM DSA
dsa_compare.GO_diff()

go = dsa_compare.get_GO_diff
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/dsa/go.bmp" alt="drawing" width="700" />
</p>




<br />

```
# KEGG DSA
dsa_compare.KEGG_diff()

kegg = dsa_compare.get_KEGG_diff
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/dsa/kegg.bmp" alt="drawing" width="700" />
</p>




<br />

```
# Reactome DSA
dsa_compare.REACTOME_diff()

reactome = dsa_compare.get_REACTOME_diff
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/dsa/reactome.bmp" alt="drawing" width="700" />
</p>




<br />

```
# Specificity (HPA) DSA
dsa_compare.spec_diff()

hpa = dsa_compare.get_specificity_diff
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/dsa/hpa.bmp" alt="drawing" width="700" />
</p>




<br />

```
# Gene interactions DSA
dsa_compare.gi_diff()

GI = dsa_compare.get_GI_diff
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/dsa/gi.bmp" alt="drawing" width="700" />
</p>




<br />

```
# Networks DSA
dsa_compare.network_diff()

networks = dsa_compare.get_networks_diff
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/dsa/net.bmp" alt="drawing" width="800" />
</p>



<br />

```
# Inter Terms DSA
dsa_compare.inter_processes()

inter_terms = dsa_compare.get_inter_terms
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/dsa/inter.bmp" alt="drawing" width="700" />
</p>



<br />

```
# Connections DSA
dsa_compare.connections_diff()

connections = dsa_compare.get_set_to_set_con
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/dsa/interconn.bmp" alt="drawing" width="700" />
</p>



<br />

```
# * all data in parallel:

dsa_compare.full_analysis()


# get_results can be used for return all DSA data like above ^^^
results3 = dsa_compare.get_results
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/dsa/dsa.bmp" alt="drawing" width="700" />
</p>



<br />

```
# import the VisualizationDES class from the Enrichment module
from gedspy import VisualizationDES

# load library JVG - display and adjustment Networks and Bar plots
from JVG import JVG

# create instance of the VisualizationDES class with results from get_results for set1 and set2 DSA results
vis_des = VisualizationDES(results3)
```


<br />

```
# Gene type
plot  =  vis_des.diff_gene_type_plot( 
                        set1_name = 'Set 1', 
                        set2_name = 'Set 2', 
                        image_width = 12, 
                        image_high = 6, 
                        font_size = 15)

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/genetype.bmp" alt="drawing" width="500" />
</p>



<br />

```
# GO-TERM
plot  =  vis_des.diff_GO_plot(   
            p_val = 0.05, 
            test = 'FISH', 
            adj = 'BH', 
            n = 25, 
            min_terms = 5,
            selected_parent = [],
            width = 10, 
            bar_width = 0.5, 
            stat = 'p_val',
            sep_factor = 50)

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/go.bmp" alt="drawing" width="500" />
</p>




<br />

```
# KEGG
plot  =  vis_des.diff_KEGG_plot(   
                p_val = 0.05, 
                test = 'FISH', 
                adj = 'BH', 
                n = 25, 
                min_terms = 2,
                selected_parent = [],
                width = 10, 
                bar_width = 0.5, 
                stat = 'p_val',
                sep_factor = 50)

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/kegg.bmp" alt="drawing" width="800" />
</p>





<br />

```
# Reactome
plot  =  vis_des.diff_REACTOME_plot(   
                    p_val = 0.05, 
                    test = 'FISH', 
                    adj = 'BH', 
                    n = 25, 
                    min_terms = 5,
                    selected_parent = [],
                    width = 10, 
                    bar_width = 0.5, 
                    stat = 'n',
                    sep_factor = 50)

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/reactome.bmp" alt="drawing" width="800" />
</p>



<br />

```
# Specificity (HPA)
plot  =  vis_des.diff_SPECIFICITY_plot(   
                    p_val = 0.05, 
                    test = 'FISH', 
                    adj = 'BH', 
                    n = 6, 
                    min_terms = 1,
                    selected_set = [],
                    width = 10, 
                    bar_width = 0.5, 
                    stat = 'p_val',
                    sep_factor = 15)

graph = JVG.MplEditor(plot)
graph.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/hpa.bmp" alt="drawing" width="800" />
</p>



<br />

```
# GO-TERM network
go = vis_des.diff_GOPa_network_create(data_set = 'GO-TERM', 
                        genes_inc = 10, 
                        gene_int = True, 
                        genes_only = True, 
                        min_con = 2, 
                        children_con = False,
                        include_childrend = True,
                        selected_parents = [],
                        selected_genes = [])

nt = JVG.NxEditor(go)
nt.edit()

```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/gonet.bmp" alt="drawing" width="600" />
</p>


<br />

```
# KEGG network
kegg = vis_des.diff_GOPa_network_create(data_set = 'KEGG', 
                        genes_inc = 10, 
                        gene_int = True, 
                        genes_only = True, 
                        min_con = 2, 
                        children_con = False,
                        include_childrend = True,
                        selected_parents = [],
                        selected_genes = [])

nt = JVG.NxEditor(kegg)
nt.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/keggnet.bmp" alt="drawing" width="800" />
</p>


<br />


```
# Reactome network
reactome = vis_des.diff_GOPa_network_create(data_set = 'REACTOME', 
                        genes_inc = 10, 
                        gene_int = True, 
                        genes_only = True, 
                        min_con = 2, 
                        children_con = False,
                        include_childrend = True,
                        selected_parents = [],
                        selected_genes = [])

nt = JVG.NxEditor(reactome)
nt.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/reactnet.bmp" alt="drawing" width="800" />
</p>


<br />


```
# GI network
gi = vis_des.diff_GI_network_create(min_con = 2)

nt = JVG.NxEditor(gi)
nt.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/ginet.bmp" alt="drawing" width="500" />
</p>


<br />


```
# AMUTO-ML network
ml = vis_des.diff_AUTO_ML_network( 
                    genes_inc = 10, 
                    gene_int = True, 
                    genes_only = True, 
                    min_con = 2, 
                    children_con = False, 
                    include_childrend = False,
                    selected_parents = [],
                    selected_genes = [])
    
nt = JVG.NxEditor(ml)
nt.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/automl.bmp" alt="drawing" width="650" />
</p>


<br />


```
# RNAseq
seq = vis_des.diff_gene_scatter( 
                 set_num = 2,
                 colors = 'viridis', 
                 species = 'human', 
                 hclust = 'complete', 
                 img_width = None, 
                 img_high = None, 
                 label_size = None, 
                 x_lab = 'Genes', 
                 legend_lab = 'log(TPM + 1)',
                 selected_list = [])
```



<br />


```
graph1 = JVG.MplEditor(seq['tissue_expression_HPA'])
graph1.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/rnaseqhpa.bmp" alt="drawing" width="800" />
</p>


<br />


```
graph2 = JVG.MplEditor(seq['tissue_expression_RNA_total_tissue'])
graph2.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/rnaseqtotal.bmp" alt="drawing" width="800" />
</p>


<br />


```
graph3 = JVG.MplEditor(seq['tissue_expression_fetal_development_circular'])
graph3.edit()
```

<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/example_2/vis/rnaseqcirc.bmp" alt="drawing" width="800" />
</p>


<br />

[Example 2 - file](examples/example_2.py)


<br />


#### Heatmap - adjusted data

```
Get data - example:

data = dsa_compare.get_full_GO()

# Adjust terms in the data (optional)

term_col = 'child_name'
set_col = 'set'
sets = {'s1':'down','s2':'up'}
title= 'BP : developmental process'
fig_size = (8,15)

figure = enrichment_heatmap(data = data, 
                       stat_col = stat_col, 
                       term_col = term_col,
                       set_col = set_col,
                       sets = sets,
                       title = title,
                       fig_size = fig_size,
                       font_size = 16,
                       scale = True) 


figure.savefig(
    "heatmap.svg",
    format="svg",
    dpi=300,
    bbox_inches="tight"
)
```


<p align="center">
<img  src="https://raw.githubusercontent.com/jkubis96/GEDSpy/refs/heads/main/fig/heatmap.svg" alt="drawing" width="450" />
</p>

        
                    
<br />

<br />

<br />


#### Have fun JBS©







