import { useState } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import ReactCardFlip from 'react-card-flip';


export default function CourseCard(props: CourseCardProps) {
  const [isFlipped, setIsFlipped] = useState(false);
  const handleFlip = () => {setIsFlipped(!isFlipped);};
  const {
    courseCode, name, subjectCode, catalogLevel, estimatedDescription,
    associatedProfessors, type, sectionNumber, location, days, time, dates,
    instructor, reviews,
  } = props;

  return (
    <ReactCardFlip isFlipped={isFlipped} flipDirection="horizontal">
      <Card style={{ maxWidth: 345, margin: '20px auto' }} onClick={handleFlip}>
        <CardContent>
          <Typography gutterBottom variant="h5" component="div"> {name} </Typography>
          <Typography variant="body2" color="textSecondary">Código: {courseCode}</Typography>
          {subjectCode && <Typography variant="body2" color="textSecondary">Área (sigla): {subjectCode}</Typography>}
          {catalogLevel && <Typography variant="body2" color="textSecondary">Nível do código: {catalogLevel}</Typography>}
          {estimatedDescription && <Typography variant="body2" sx={{ mt: 1 }}>Descrição estimada: {estimatedDescription}</Typography>}
          {associatedProfessors.length > 0 && (
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Professores associados nos dados históricos: {associatedProfessors.join(', ')}
            </Typography>
          )}
          {type && <Typography variant="body2" color="textSecondary">Tipo: {type}</Typography>}
          {sectionNumber && <Typography variant="body2" color="textSecondary">Turma: {sectionNumber}</Typography>}
          {location && <Typography variant="body2" color="textSecondary">Local: {location}</Typography>}
          {days && <Typography variant="body2" color="textSecondary">Dias: {days}</Typography>}
          {time && <Typography variant="body2" color="textSecondary">Horário: {time}</Typography>}
          {dates && <Typography variant="body2" color="textSecondary">Datas: {dates}</Typography>}
          {instructor && <Typography variant="body2" color="textSecondary">Instrutor atual: {instructor}</Typography>}
        </CardContent>
      </Card>

      <Card style={{ maxWidth: 345, margin: '20px auto' }} onClick={handleFlip}>
        <CardContent>
          <Typography gutterBottom variant="h5" component="div"> Reviews </Typography>
          {reviews.map((review, index) => ( 
            <Typography key={index} variant="body2" color="textSecondary" component="p"> {review}</Typography>
          ))}
        </CardContent>
      </Card>
    </ReactCardFlip>
  );
}
