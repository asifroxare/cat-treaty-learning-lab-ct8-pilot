import { readFileSync } from "node:fs";

const source = readFileSync(new URL("../src/scenarios/guided.ts", import.meta.url), "utf8");
const prohibited = ["recommended", "should choose", "best option", "optimal structure", "prefer this election"];
const found = prohibited.filter((form) => source.toLowerCase().includes(form));
if (found.length) throw new Error(`Guided content contains prohibited recommendation/ranking forms: ${found.join(", ")}`);
const experimentCount = (source.match(/id: "E0[1-7]"/g) ?? []).length;
if (experimentCount !== 7) throw new Error(`Expected seven guided experiments; found ${experimentCount}`);
console.log("CT7 guided-content neutrality: PASS");
