"use strict";

const chalk = require("chalk");
const fs = require("fs");
const path = require("path");

let files = fs.readdirSync(path.join(__dirname, "db"));

const containers = {};
const locations = {};

files.filter((a) => a.endsWith("json")).forEach((id) => {
    let file = require(path.join(__dirname, "db", id));
    if (file.class == "Thing") {
        if (file.location != undefined && file.location != "lhq-returns") {
            if (locations[file.location] == undefined) {
                locations[file.location] = new Set();
            }
            locations[file.location].add(file.id);
        }
    } else if (file.class == "Container") {
        containers[id] = true;
    }
});

Object.entries(locations).forEach(([loc, items]) => {
    if (!containers[loc]) {
        console.log("\n", chalk.red(loc, "has"));
        items.forEach((item) => {
            console.log("   ", item);
        });
    }
})