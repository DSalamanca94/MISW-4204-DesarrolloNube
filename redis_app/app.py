from flask import Flask

app = Flask(__name__)

@app.route('/')
def convert():
    def get(self, id_task):
        try:
            document = Document.query.get(id_task)

            if not document:
                return {'error': 'Document not found'}, 404

            if document.user_id != user_id:
                return {'error': 'Unauthorized access to this document'}, 403
            
            input_filename = document.location_in
            output_filename = f"{document.id}.{document.format_out.value}"
            output_filename = os.path.join(_download_directory, output_filename)

            with open(output_filename, "wb") as out_file:
                out_file.close()

            print(f'{input_filename =}')

            ffmpeg_command = ['ffmpeg', '-i', input_filename, output_filename, '-y']

            return_code = subprocess.call(ffmpeg_command)

            with open(output_filename, "rb") as output_file:
                document.file_out = output_file.read()

            print('this sheet has run')
            print(return_code)

            print('out',output_filename)

            db.session.commit()
            return send_file(output_filename, as_attachment=True)

        except Exception as e:
            print('error', e)
            return {'error': str(e)}, 400