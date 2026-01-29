use pyo3::prelude::*;

/// Calculates a long-term heatmap based on the provided bounding boxes and shape.
///
/// # Arguments
/// * `boxes` - A vector of tuples representing bounding boxes. Each tuple contains four integers
/// (x1, y1, x2, y2).
/// * `shape` - A tuple representing the shape of the heatmap (height, width).
///
/// # Returns
/// A 2D vector representing the heatmap.
#[pyfunction]
fn calc_longterm_heatmap(boxes: Vec<(i32, i32, i32, i32)>, shape: (i32, i32)) -> Vec<Vec<i32>> {
    let width = shape.1 as usize;
    let height = shape.0 as usize;
    // NOTE: This is to avoid nested vectors
    let mut heatmap: Vec<i32> = vec![0; width * height];
    println!("Calculate heatmap for shape {:?}", shape);

    for detect in boxes {
        let (x1, y1, x2, y2) = detect;
        let center = ((x1 + x2) / 2, (y1 + y2) / 2);
        let radius = ((x2 - x1).min(y2 - y1)) / 2;

        if radius <= 0 {
            continue;
        }

        let radius_squared = radius.pow(2);
        let (x_min, x_max) = (
            (center.0 - radius).max(0),
            (center.0 + radius).min(shape.1 - 1),
        );
        let (y_min, y_max) = (
            (center.1 - radius).max(0),
            (center.1 + radius).min(shape.0 - 1),
        );

        for y in y_min..=y_max {
            for x in x_min..=x_max {
                if (x - center.0).pow(2) + (y - center.1).pow(2) <= radius_squared {
                    let index = (y as usize) * width + (x as usize);
                    heatmap[index] += 2;
                }
            }
        }
    }

    (0..height)
        .map(|i| heatmap[i * width..(i + 1) * width].to_vec())
        .collect()
}

#[pymodule]
fn heatmapcalc(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calc_longterm_heatmap, m)?)?;
    Ok(())
}
