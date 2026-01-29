import type { FileData } from "@gradio/client";
import Box from "./Box";
import Point from "./Point";

export default class AnnotatedImageData {
  image: FileData;
  boxes: Box[] = [];
  points: Point[] = [];
  orientation = 0;
}
