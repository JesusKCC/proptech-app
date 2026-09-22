import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;
    const slug = (formData.get('slug') as string) || 'plano';

    if (!file) {
      return NextResponse.json({ error: 'No se envió ningún archivo' }, { status: 400 });
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return NextResponse.json({ error: 'Solo se permiten archivos en formato PDF' }, { status: 400 });
    }

    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    // Ensure public/blueprints directory exists
    const blueprintsDir = path.join(process.cwd(), 'public', 'blueprints');
    if (!fs.existsSync(blueprintsDir)) {
      fs.mkdirSync(blueprintsDir, { recursive: true });
    }

    // Clean filename
    const cleanSlug = slug.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
    const fileName = `${cleanSlug}.pdf`;
    const filePath = path.join(blueprintsDir, fileName);

    // Save PDF file to public/blueprints/
    await fs.promises.writeFile(filePath, buffer);

    const publicUrl = `/blueprints/${fileName}`;

    return NextResponse.json({
      success: true,
      url: publicUrl,
      fileName,
      sizeBytes: file.size,
    });
  } catch (error: any) {
    console.error('Error uploading blueprint PDF:', error);
    return NextResponse.json(
      { error: 'Error al procesar y guardar el plano PDF', details: error.message },
      { status: 500 }
    );
  }
}
