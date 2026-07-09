/**
 * 将数组按 size 切分为二维数组（用于卡片网格按行渲染）
 */
export function splitArray<T>(arr: T[], size: number): T[][] {
  const result: T[][] = []
  for (let i = 0; i < arr.length; i += size) {
    result.push(arr.slice(i, i + size))
  }
  return result
}
