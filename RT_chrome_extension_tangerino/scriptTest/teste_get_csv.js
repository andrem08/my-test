const dfd = require("danfojs-node");

const url = "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv";

dfd.readCSV(url)
  .then(df => {
    df.head().print(); 
    console.log(df.shape);
  })
  .catch(err => {
    console.log(err);
  });