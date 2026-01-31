
#ifdef USE_VTK

    #include <finelc/matrix.h>
    #include <finelc/enumerations.h>

    #include <finelc/mesh/mesh.h>
    #include <finelc/elements/element.h>
    #include <finelc/analysis/analysis.h>

    #include <finelc/result/result.h>

    #include <memory>
    #include <cmath>

    #include <vtkSmartPointer.h>
    #include <vtkPoints.h>
    #include <vtkDoubleArray.h>
    #include <vtkPolyData.h>
    #include <vtkPointData.h>

    #include <vtkVertexGlyphFilter.h>
    #include <vtkPolyDataMapper.h>
    #include <vtkActor.h>
    #include <vtkRenderer.h>
    #include <vtkRenderWindow.h>
    #include <vtkRenderWindowInteractor.h>
    #include <vtkLine.h>
    #include <vtkCellArray.h>
    #include <vtkProperty.h>


    namespace finelc{

        void StaticResult::plot_2D_grid(ResultData id, int internal_pts, bool show_edges, bool show_nodes) const {
        SupportFn support_func = get_support_func(id);
        EvalFnPtr eval_func = get_eval_func(id);

        auto renderer = vtkSmartPointer<vtkRenderer>::New();

        // Single containers for all points and scalar values
        auto allPoints = vtkSmartPointer<vtkPoints>::New();
        auto allValues = vtkSmartPointer<vtkDoubleArray>::New();
        allValues->SetName("Values");

        int pointOffset = 0;

        // For polygon edges
        auto edgePoints = vtkSmartPointer<vtkPoints>::New();
        auto edgeLines = vtkSmartPointer<vtkCellArray>::New();
        int edgeOffset = 0;

        for (int el_number = 0; el_number < analysis->number_of_elements(); ++el_number) {
            IElement_ptr el = analysis->get_element(el_number);

            if (!((*el).*support_func)())
                continue;

            Vector ue = analysis->get_element_ue(U, el_number);
            std::vector<Point> grid = create_grid(internal_pts, el->number_of_dimensions(), el->get_integration_domain());

            // Insert points and scalar values
            for (auto& pt : grid) {
                Point gpt = el->local_to_global(pt);
                allPoints->InsertNextPoint(gpt.x, gpt.y, 0.0);
                double value = eval_func(pt.as_vector(), ue, el);
                allValues->InsertNextValue(value);
            }

            // Insert polygon edges
            const VectorNodes& nodes = el->get_nodes();
            std::vector<Line_ptr> lines = el->edges();
            int nVerts = lines.size();
            for (auto& line : lines){
                const Point& v = line->p1;
                edgePoints->InsertNextPoint(v.x, v.y, 0.0);
            }

            
            for (int i = 0; i < nVerts; ++i) {
                auto line = vtkSmartPointer<vtkLine>::New();
                line->GetPointIds()->SetId(0, edgeOffset + i);
                line->GetPointIds()->SetId(1, edgeOffset + (i + 1) % nVerts);
                edgeLines->InsertNextCell(line);
            }
            edgeOffset += nVerts;
        }

        // Create polydata for points (interior coloring)
        auto polyData = vtkSmartPointer<vtkPolyData>::New();
        polyData->SetPoints(allPoints);
        polyData->GetPointData()->SetScalars(allValues);

        // Use vertex glyph filter to render points
        auto vertexFilter = vtkSmartPointer<vtkVertexGlyphFilter>::New();
        vertexFilter->SetInputData(polyData);
        vertexFilter->Update();

        auto mapper = vtkSmartPointer<vtkPolyDataMapper>::New();
        mapper->SetInputConnection(vertexFilter->GetOutputPort());
        mapper->SetScalarRange(allValues->GetRange());

        auto actor = vtkSmartPointer<vtkActor>::New();
        actor->SetMapper(mapper);
        renderer->AddActor(actor);

        // Create polydata for edges
        if(show_edges){
            auto edgePolyData = vtkSmartPointer<vtkPolyData>::New();
            edgePolyData->SetPoints(edgePoints);
            edgePolyData->SetLines(edgeLines);

            auto edgeMapper = vtkSmartPointer<vtkPolyDataMapper>::New();
            edgeMapper->SetInputData(edgePolyData);

            auto edgeActor = vtkSmartPointer<vtkActor>::New();
            edgeActor->SetMapper(edgeMapper);
            edgeActor->GetProperty()->SetColor(0, 0, 255);
            edgeActor->GetProperty()->SetLineWidth(2);

            renderer->AddActor(edgeActor);
        }

        if(show_nodes){
            auto nodePolyData = vtkSmartPointer<vtkPolyData>::New();
            nodePolyData->SetPoints(edgePoints);

            auto nodeVertexFilter = vtkSmartPointer<vtkVertexGlyphFilter>::New();
            nodeVertexFilter->SetInputData(nodePolyData);
            nodeVertexFilter->Update();

            auto nodeMapper = vtkSmartPointer<vtkPolyDataMapper>::New();
            nodeMapper->SetInputConnection(nodeVertexFilter->GetOutputPort());

            auto nodeActor = vtkSmartPointer<vtkActor>::New();
            nodeActor->SetMapper(nodeMapper);
            nodeActor->GetProperty()->SetColor(0, 0, 0);
            nodeActor->GetProperty()->SetPointSize(5);

            renderer->AddActor(nodeActor);
        }

        // Render window
        auto window = vtkSmartPointer<vtkRenderWindow>::New();
        window->AddRenderer(renderer);
        window->SetSize(1600, 1200);

        auto interactor = vtkSmartPointer<vtkRenderWindowInteractor>::New();
        interactor->SetRenderWindow(window);

        window->Render();
        interactor->Initialize(); // non-blocking
    }

    } // namespace finelc

#endif