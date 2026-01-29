# pEEGy
![](doc/_static/peegy.png)

Tools for analysing EEG data and generate pipelines in python. 
At the moment we work with EDF and BDF, but you can also read whatever data you have and plug it into a pipeline.

The pEEGy steps are basically:
1) Load BDF/EDF files (raw data)
2) Define your pipeline for EEG-Analysis (Referencing EEG using predefined EEG Cap Layouts,
 creating Epochs based on trigger events, down-sampling, removing artifacts, defining Regions
 of Interest, Statistics to run on the epochs, or plot the data)
3) Define in which database you want to save the results
4) Run the above steps.

Examples can be found in [pEEGy](https://open-source-brain.gitlab.io/peegy/) website. 

## Installation
This software requires Python >= 3.9

Standard installation of stable release can be obtained from the official repository 
```commandline
pip install peegy
```
### Windows enviroment
The easiest and painless installation is via [Anaconda](https://www.anaconda.com/products/distribution).
Once you have installed Anaconda, create a new python environment and launch the terminal in this environment.
In the terminal run: 
```commandline
pip install peegy
```
pEEGy will be installed in that new environment. 


## Pipeline diagrams
To generate pipeline diagrams, you will need to install [Graphviz](https://graphviz.org/download/)

## Development version
The development version can be obtained from our official Gitlab repository 

```commandline
git clone https://gitlab.com/open-source-brain/peegy.git
```

This will clone into the folder 'pEEGy'.

To be able to look in the (generated) sql-databases, we recommend using DB Browser (https://sqlitebrowser.org/)

### For Windows

Precompiled PyFFTW is easier to install via conda.
If you are using window, this is the easiest way to have PyFFT running.

```commandline
conda install -c conda-forge pyfftw
```

## Examples
Please have a look at the 'examples' folder for different EEG analysis examples in the time or frequency domain.

## Sidekicks 
We have also created other tools for EEG experiments. 
- If you have a [Biosemi](https://www.biosemi.com/) EEG system, you can use [BiosemiRealtime](https://gitlab.com/jundurraga/biosemi_real_time) 
to allow realtime processing in the time- and frequency-domain.
- If use are running auditory EEG experiments such as auditory brainstem responses (ABRs), auditory steady-state 
responses (ASSRs), frequency-following responses (FFRs), auditory change complex (ACC), and other auditory evoked
responses. We have a matlab toolbox [AEP_GUI](https://gitlab.com/jundurraga/ucl-matlab) to generate and present 
these stimuli in a reliable way. 
