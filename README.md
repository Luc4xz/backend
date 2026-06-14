When I first examined and downloaded the files of dataset from the SciSciNet in HuggingFace, I transferred them from .parquet to .csv to help me beter convert them into .json file.<br>

Then I used Python scripts to tansfer .csv files into .json that can be display in the website. Only the fields needed for visualization, such as paper IDs, publication years, author IDs are extracted. I also removed duplicated records, filtered papers by year, and excluded extremely large papers or author groups including almost every reputational universities in the world that are irrevalent, more importantly, would make the network too dense and crash. <br>

Since there is a maximum size for file uploaded into Github also those files are too large to load all at once in the browser, I divided each large json file into several small files. I organized the data by year and by visualization purpose. For example, I created a smaller overview file such as citation_network_top500.json for the initial visualization, and then designed the website to load additional data only when the user clicks a “Load More Data” button. This helped reduce the initial loading time and made the website more responsive. <br>

For the visualization part, due to the limited time period, I only implement the requiement from specification to maintain the basic function. The citation network represents papers as nodes and citation relationships as edges, while the author collaboration network represents authors as nodes and co-authorship relationships as edges. I also added interactive functions such as draggable nodes, hover tooltips, zooming, filtering, and detail-on-demand so users can explore the data more actively instead of only viewing a static graph.<br>

However, one major challenge I encountered was scalability. When the network included more than around 2,000 nodes, the framerate dropped significantly, making reader harder to maintain feeling comfortable. So I decided to turn visulization of networkswhich contain more than 2000 nodes into static pictures after rendering for the first few seconds. <br>


However, despite many attempts i have tried, I couldn't find a doable way to implement clear visualization like edge bundling technique to display the node clusters more distinguishable. They all seem like crowd togwther when applying the filter to more than 2000. 
