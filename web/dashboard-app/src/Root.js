/* React */
import React, { useState, useEffect } from 'react';
/* Material UI Components */
import { makeStyles } from '@material-ui/core/styles';
import Container from '@material-ui/core/Container';
import { Responsive, WidthProvider } from 'react-grid-layout';
/* Local modules */
import Chart from './Chart';
import Header from './Header';
import { loadCharts } from './Questions';
import Questions from './Questions';
import API from './API';

const ResponsiveGridLayout = WidthProvider(Responsive);

const useStyles = makeStyles(theme => ({
    chartContainer: {
    },
}));
function Root() {
    const classes = useStyles();
    const [ charts, setCharts ] = useState([]);
    const [ layouts, setLayouts ] = useState({"lg":[{"w":2,"h":1,"x":0,"y":0,"i":"0","moved":false,"static":false},{"w":2,"h":1,"x":1,"y":0,"i":"1","moved":false,"static":false}]});
    const [ fullScreenLayouts, setFullScreenLayouts ] = useState(undefined);
    const [ api, setAPI ] = useState({});

    useEffect(() => {
        setAPI(new API());
    }, []);

    async function onQuestionChange(element, question) {
        try {
            setCharts(await loadCharts(api, question.id));
        } catch(e) {
            console.error('Something went wrong when trying to fetch the question, %s', e);
        }
    }

    function changeFullScreen(isFullScreen, key) {
        const layout = layouts.lg;
        if (isFullScreen) {
            setFullScreenLayouts({
                lg: [
                    {
                        ...(layout[0]),
                        w: 3,
                        h: 2,
                    },
                    layout[1]
                ]
            });
        } else {
            setFullScreenLayouts(undefined);
        }
    }

    function onLayoutChange(_, layouts) {
        if (!fullScreenLayouts) setLayouts(layouts);
    }

    return (
        <React.Fragment>
            <Header>
                <Questions onQuestionChange={onQuestionChange} />
            </Header>
            <Container maxWidth={false}>
                <ResponsiveGridLayout
                    breakpoints={{lg: 1080, md: 768, sm: 600, xs: 400, xxs: 0}}
                    cols={{lg: 3, md: 3, sm: 2, xs: 1, xxs: 1}}
                    rowHeight={400}
                    layouts={fullScreenLayouts || layouts}
                    onLayoutChange={onLayoutChange}
                >
                    {
                        charts.map((chart, id) => <div className={classes.chartContainer} key={id}><Chart chartData={chart} changeFullScreen={(isFullScreen) => changeFullScreen(isFullScreen, id)} /></div>)
                    }
                </ResponsiveGridLayout>
            </Container>
        </React.Fragment>
    );
}

export default Root;
