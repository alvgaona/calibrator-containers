// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from "next";
import { cv } from "opencv-wasm";

type Data = {
  message: string;
};

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse<Data>,
) {
  let mat = cv.matFromArray(2, 3, cv.CV_8UC1, [1, 2, 3, 4, 5, 6]);

  res
    .status(200)
    .json({
      message: `I'm an OpenCV matrix with size ${(mat.rows, mat.cols)}`,
    });
}
