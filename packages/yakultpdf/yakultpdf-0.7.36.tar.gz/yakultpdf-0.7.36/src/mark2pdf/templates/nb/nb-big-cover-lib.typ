// nb-big-cover-lib.typ - NB Big Cover Style
// Based on nb-cover-lib.typ, modified for full-width fixed-position image

//显示封面的图片
#let coverhero(hero-image: none) = {
  // Not used in this style, but kept for reference if needed
}

#let coverquote(description) = {
  box(inset: (x: 0.4em, y: 12pt), width: 100%, {
    text(1.2em, fill: white, align(left, description))
  })
}

#let covertitle(
  title: none,
  titlefont: none,
) = {
  // Reverted to default colors
  set text(font: titlefont, size: 28pt, tracking: -1pt, weight: "semibold", fill: white)
  block(
    height: 4em,
    width: 110%,
    par(
      leading: 0.5em,
      first-line-indent: 0em,
      align(left + horizon, text(title)),
    ),
  )
}

#let coverinfo(
  publication-info: none,
  date: none,
) = {
  set par(first-line-indent: 0em)
  set text(0.7em, fill: white)
  block({
    v(1fr) //位于页面底部
    move(dx: 20%, dy: 0%, [#publication-info #v(0.2em) #date])
  })
}

//创建封面页的函数
#let coverpage(
  title: none,
  author: none,
  edition: none,
  hero-image: none,
  description: none,
  publication-info: none,
  date: none,
  logo: none,
  font: none,
  titlefont: none,
  coverbg: none,
) = {
  // Determine background
  // If coverbg is provided, use it. Keep the red bar on the right.
  let bg-image = if coverbg != none {
    image(coverbg, width: 100%, height: 100%, fit: "cover")
  } else {
    // Default None (white background) if no image provided
    none
  }

  // 设置首页面格式
  set page(
    width: 210mm,
    height: 297mm,
    margin: (left: 2.5cm, top: 2.5cm, right: 2.5cm, bottom: 2.5cm),
    header: none,
    background: {
      bg-image
      place(top, rect(
        fill: rgb("#4CA572"),
        height: 100%,
        width: 100%,
      ))
    },
  )

  set text(
    lang: "zh",
    font: font,
    size: 12pt,
    alternates: false,
    // fill: white, // Reverted: use default color
  )

  // 2. 独立放置图片 (图片放在最顶部，全宽出血)
  if hero-image != none {
    // Page width: 210mm. Left margin: 2.5cm. Top margin: 2.5cm.
    // To bleed left: dx: -2.5cm.
    // To bleed top: dy: -2.5cm.
    place(top, dy: -2.5cm, dx: -2.5cm, {
      set image(width: 210mm) // Full Page Width
      hero-image.image
    })
  }

  grid(
    columns: (1fr, 7.8cm - 1.6cm - 18pt),
    column-gutter: 36pt,
    row-gutter: 32pt,

    // Row 1 Col 1: Spacer for Image area (Image is Top Bleed)
    // 10cm spacer to push content down below image
    v(10cm),

    // Row 1 Col 2: Sidebar (None)
    none,

    // Row 2 Col 1: Title (Below Image)
    covertitle(
      title: title,
      titlefont: titlefont,
    ),

    // Row 2 Col 2: Sidebar (None)
    none,

    // Row 3 Col 1: Description Quote (Below Title)
    coverquote(description),

    // Row 3 Col 2: Sidebar (None)
    none,
  )

  place(
    bottom,
    dy: 1cm,
    grid(
      columns: (1fr, 7.8cm - 1.6cm - 18pt),
      column-gutter: 36pt,
      row-gutter: 32pt,
      //logo
      block(width: 3cm, logo),
      // edition info and publication info
      block({
        // text(fill: white, weight: "medium", 14pt, align(right, edition))
        v(0.5em)
        coverinfo(publication-info: publication-info, date: date)
      }),
    ),
  )
}
