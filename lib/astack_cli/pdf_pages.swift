// usage: swift pdf_pages.swift <pdf> <outdir> <maxdim>
// 쪽마다 page-NNN.png를 쓰고 파일 이름을 한 줄씩 출력한다.
import AppKit
import PDFKit

let a = CommandLine.arguments
guard a.count == 4, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
    FileHandle.standardError.write("PDF를 열 수 없습니다\n".data(using: .utf8)!)
    exit(2)
}
let out = URL(fileURLWithPath: a[2])
let maxDim = CGFloat(Double(a[3]) ?? 2200)
for i in 0..<doc.pageCount {
    guard let page = doc.page(at: i) else { continue }
    let box = page.bounds(for: .mediaBox)
    let scale = maxDim / max(box.width, box.height)
    let w = Int(box.width * scale), h = Int(box.height * scale)
    guard let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8,
                                     samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                                     colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0),
          let ctx = NSGraphicsContext(bitmapImageRep: rep) else { exit(1) }
    let cg = ctx.cgContext
    cg.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    cg.fill(CGRect(x: 0, y: 0, width: w, height: h))
    cg.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: cg)
    guard let png = rep.representation(using: .png, properties: [:]) else { exit(1) }
    let name = String(format: "page-%03d.png", i + 1)
    try! png.write(to: out.appendingPathComponent(name))
    print(name)
}
